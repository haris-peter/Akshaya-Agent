import uuid
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.schemas import (
    DocumentUploadRequest, DocumentUploadResponse,
    OCRWebhookRequest, OCRWebhookResponse
)
from app.db.session import get_session
from app.db.models import DocumentUpload, Citizen

router = APIRouter()


def _generate_presigned_url(s3_key: str) -> str:
    """
    TODO: Replace with real S3 presigned URL generation when bucket is configured.
    Example using boto3:
        import boto3
        s3 = boto3.client("s3", region_name="ap-south-1")
        return s3.generate_presigned_url(
            "put_object",
            Params={"Bucket": "your-bucket-name", "Key": s3_key},
            ExpiresIn=300
        )
    """
    return f"https://your-s3-bucket.s3.ap-south-1.amazonaws.com/{s3_key}?stub=pending_s3_config"


@router.post("/upload-url", response_model=DocumentUploadResponse)
async def generate_upload_url(request: DocumentUploadRequest, db: AsyncSession = Depends(get_session)):
    """
    Step 1 of webhook flow:
    Client calls this to get a presigned S3 URL.
    A DocumentUpload record is created with status='pending'.
    After the client uploads the file to S3, Tesseract OCR processes it
    and calls back POST /api/v1/documents/webhooks/ocr-complete with the result.
    """
    citizen_result = await db.execute(
        select(Citizen).where(Citizen.aadhar_number == request.citizen_id)
    )
    citizen = citizen_result.scalars().first()

    upload_id = f"UPL-{uuid.uuid4().hex[:8].upper()}"
    s3_key = f"documents/{request.citizen_id}/{upload_id}_{request.filename}"
    presigned_url = _generate_presigned_url(s3_key)

    doc = DocumentUpload(
        upload_id=upload_id,
        citizen_id=citizen.id if citizen else None,
        s3_key=s3_key,
        status="pending"
    )
    db.add(doc)
    await db.commit()

    return DocumentUploadResponse(
        upload_id=upload_id,
        presigned_url=presigned_url,
        message="Upload URL generated. PUT your file to the URL, then Tesseract will call back the webhook."
    )


@router.post("/webhooks/ocr-complete", response_model=OCRWebhookResponse)
async def ocr_webhook(request: OCRWebhookRequest, db: AsyncSession = Depends(get_session)):
    """
    Step 2 of webhook flow:
    Tesseract OCR Lambda/service calls this endpoint when processing completes.
    Updates the DocumentUpload record with OCR text and sets status to 'completed' or 'failed'.
    The vault_tool polls GET /status/{upload_id} to detect when this fires.
    """
    result = await db.execute(
        select(DocumentUpload).where(DocumentUpload.upload_id == request.upload_id)
    )
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Upload record '{request.upload_id}' not found.")

    doc.status = request.status
    if request.status == "completed" and request.ocr_text:
        doc.ocr_text = request.ocr_text

    await db.commit()

    return OCRWebhookResponse(
        status="success",
        message=f"Upload {request.upload_id} updated to '{request.status}'."
    )


@router.get("/{upload_id}/status")
async def get_upload_status(upload_id: str, db: AsyncSession = Depends(get_session)):
    """
    Polling endpoint: vault_tool uses this to wait for OCR webhook completion.
    Returns status and ocr_text when status='completed'.
    """
    result = await db.execute(
        select(DocumentUpload).where(DocumentUpload.upload_id == upload_id)
    )
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Upload {upload_id} not found.")
    return {
        "upload_id": upload_id,
        "status": doc.status,
        "ocr_text": doc.ocr_text if doc.status == "completed" else None
    }
