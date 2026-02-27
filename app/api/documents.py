import json
import httpx
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from app.db.session import get_session
from app.db.models import Document, Citizen, Requirement

router = APIRouter()

TESSERACT_LAMBDA_URL = "https://cwtrytr9te.execute-api.ap-south-1.amazonaws.com/upload"


def _build_rag_json(requirement_name: str, doc_type_slug: str, ocr_text: str) -> dict:
    """
    Converts raw OCR text into a structured JSON payload ready for RAG compliance assessment.
    Format: {requirement_name: {doc_type, raw_text, summary_lines}}
    """
    lines = [l.strip() for l in ocr_text.splitlines() if l.strip()]
    return {
        requirement_name: {
            "doc_type": doc_type_slug,
            "raw_text": ocr_text,
            "summary_lines": lines[:30],
            "char_count": len(ocr_text)
        }
    }


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    citizen_aadhar: str = Form(...),
    requirement_id: int = Form(...),
    db: AsyncSession = Depends(get_session)
):
    """
    Uploads a document to the Tesseract Lambda API.
    - Saves a Document record with status='processing' and the returned job_id.
    - Returns job_id so the client can correlate the webhook callback.
    """
    citizen_result = await db.execute(
        select(Citizen).where(Citizen.aadhar_number == citizen_aadhar)
    )
    citizen = citizen_result.scalars().first()
    if not citizen:
        raise HTTPException(status_code=404, detail=f"Citizen {citizen_aadhar} not found.")

    req_result = await db.execute(
        select(Requirement).where(Requirement.id == requirement_id)
    )
    requirement = req_result.scalars().first()
    if not requirement:
        raise HTTPException(status_code=404, detail=f"Requirement {requirement_id} not found.")

    existing = await db.execute(
        select(Document).where(
            Document.citizen_id == citizen.id,
            Document.requirement_id == requirement_id,
            Document.status == "completed"
        )
    )
    existing_doc = existing.scalars().first()
    if existing_doc:
        return {
            "already_exists": True,
            "job_id": existing_doc.job_id,
            "file_url": existing_doc.file_url,
            "status": existing_doc.status,
            "message": f"'{requirement.name}' already uploaded and processed for this citizen."
        }

    file_bytes = await file.read()
    filename = file.filename or f"upload_{requirement_id}.pdf"

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            TESSERACT_LAMBDA_URL,
            headers={
                "x-filename": filename,
                "Content-Type": file.content_type or "application/pdf"
            },
            content=file_bytes
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Tesseract Lambda error: {response.text[:200]}"
        )

    ocr_response = response.json()
    job_id = ocr_response.get("job_id")
    s3_url = ocr_response.get("s3_url")

    doc = Document(
        citizen_id=citizen.id,
        requirement_id=requirement_id,
        document_name=requirement.name,
        job_id=job_id,
        file_url=s3_url,
        status="processing"
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    return {
        "already_exists": False,
        "document_id": doc.id,
        "job_id": job_id,
        "s3_url": s3_url,
        "status": "processing",
        "message": "File uploaded. OCR in progress. Await webhook callback."
    }


class OCRWebhookPayload(BaseModel):
    job_id: str
    status: str
    ocr_text: Optional[str] = None
    error_message: Optional[str] = None


@router.post("/webhook")
async def ocr_webhook(payload: OCRWebhookPayload, db: AsyncSession = Depends(get_session)):
    """
    Tesseract Lambda calls this endpoint after OCR completes.
    - Matches job_id to the Document record.
    - Stores raw OCR text.
    - Generates a structured RAG-ready JSON summary and stores it in ocr_summary.
    """
    result = await db.execute(
        select(Document).where(Document.job_id == payload.job_id)
    )
    doc = result.scalars().first()

    if not doc:
        raise HTTPException(
            status_code=404,
            detail=f"No document found for job_id '{payload.job_id}'."
        )

    doc.status = payload.status

    if payload.status == "completed" and payload.ocr_text:
        req_result = await db.execute(
            select(Requirement).where(Requirement.id == doc.requirement_id)
        )
        req = req_result.scalars().first()

        doc_type_slug = ""
        if req and req.doc_type:
            doc_type_slug = req.doc_type.slug

        rag_json = _build_rag_json(
            requirement_name=doc.document_name,
            doc_type_slug=doc_type_slug,
            ocr_text=payload.ocr_text
        )
        doc.ocr_summary = json.dumps(rag_json)

    elif payload.status == "failed":
        doc.ocr_summary = json.dumps({"error": payload.error_message or "OCR failed."})

    await db.commit()

    return {
        "status": "received",
        "job_id": payload.job_id,
        "document_id": doc.id,
        "message": f"Document '{doc.document_name}' updated to '{payload.status}'."
    }


@router.get("/status/{job_id}")
async def get_document_status(job_id: str, db: AsyncSession = Depends(get_session)):
    """
    Poll endpoint — check OCR status and retrieve the RAG summary once completed.
    """
    result = await db.execute(
        select(Document).where(Document.job_id == job_id)
    )
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")

    return {
        "job_id": job_id,
        "document_id": doc.id,
        "document_name": doc.document_name,
        "status": doc.status,
        "file_url": doc.file_url,
        "ocr_summary": json.loads(doc.ocr_summary) if doc.ocr_summary else None
    }


@router.get("/citizen/{citizen_aadhar}")
async def get_citizen_documents(citizen_aadhar: str, db: AsyncSession = Depends(get_session)):
    """
    Returns all documents uploaded by a citizen, with their OCR status.
    Used by vault_tool to check what's already been processed.
    """
    citizen_result = await db.execute(
        select(Citizen).where(Citizen.aadhar_number == citizen_aadhar)
    )
    citizen = citizen_result.scalars().first()
    if not citizen:
        raise HTTPException(status_code=404, detail="Citizen not found.")

    docs_result = await db.execute(
        select(Document).where(Document.citizen_id == citizen.id)
    )
    docs = docs_result.scalars().all()

    return [
        {
            "id": d.id,
            "requirement_id": d.requirement_id,
            "document_name": d.document_name,
            "job_id": d.job_id,
            "file_url": d.file_url,
            "status": d.status,
            "has_ocr": d.ocr_summary is not None
        }
        for d in docs
    ]
