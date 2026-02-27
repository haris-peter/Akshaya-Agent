from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json

from app.api.schemas import SubmitRequest, SubmitResponse, RequirementIn, DocumentTypeIn
from app.db.session import get_session
from app.db.models import Citizen, Employee, Requirement, StatusTracking, DocumentType
from app.tools.vault_tool import vault_tool
from app.tools.explanation_tool import explanation_tool

router = APIRouter()


@router.post("/submit", response_model=SubmitResponse)
async def submit_document_request(request: SubmitRequest, db: AsyncSession = Depends(get_session)):
    citizen_result = await db.execute(
        select(Citizen).where(Citizen.aadhar_number == request.aadhar_number)
    )
    citizen = citizen_result.scalars().first()
    if not citizen:
        raise HTTPException(status_code=404, detail=f"Citizen with Aadhar {request.aadhar_number} not found.")

    reqs_result = await db.execute(
        select(Requirement).where(Requirement.doc_type == request.document_request_type)
    )
    requirements = reqs_result.scalars().all()

    tracking = StatusTracking(
        citizen_id=citizen.id,
        document_request_type=request.document_request_type,
        status="pending"
    )
    db.add(tracking)
    await db.flush()

    state = {
        "aadhar_number": request.aadhar_number,
        "document_request_type": request.document_request_type,
        "citizen": {
            "id": citizen.id, "name": citizen.name,
            "aadhar_number": citizen.aadhar_number,
            "district": citizen.district, "email": citizen.email,
        },
        "tracking_id": tracking.id,
        "requirements": [
            {"id": r.id, "name": r.name, "doc_type": r.doc_type,
             "ocr_mode": r.ocr_mode, "description": r.description,
             "is_mandatory": r.is_mandatory}
            for r in requirements
        ],
        "uploaded_files": {},
        "vault_summaries": {},
        "compliance_report": {},
        "status": "pending",
        "progress_log": ["Request initiated."]
    }

    state = await vault_tool(state)
    state = await explanation_tool(state)

    compliance_json = json.dumps(state.get("compliance_report", {}))
    vault_json = json.dumps(state.get("vault_summaries", {}))

    tracking.status = "in_review"
    tracking.vault_summary = vault_json
    tracking.compliance_notes = compliance_json
    await db.commit()

    return SubmitResponse(
        tracking_id=tracking.id,
        status="in_review",
        message="Document request submitted and processed successfully.",
        compliance_report=state.get("compliance_report", {})
    )


@router.get("/citizens")
async def list_citizens(db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Citizen))
    citizens = result.scalars().all()
    return [{"id": c.id, "name": c.name, "aadhar_number": c.aadhar_number, "district": c.district} for c in citizens]


@router.get("/employees")
async def list_employees(db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Employee).where(Employee.is_active == True))
    employees = result.scalars().all()
    return [{"id": e.id, "name": e.name, "department": e.department, "position": e.position, "email": e.email} for e in employees]


@router.get("/tracking")
async def list_tracking(db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(StatusTracking))
    records = result.scalars().all()
    return [
        {
            "id": r.id, "citizen_id": r.citizen_id, "employee_id": r.employee_id,
            "document_request_type": r.document_request_type, "status": r.status,
            "remarks": r.remarks, "created_at": str(r.created_at), "updated_at": str(r.updated_at)
        }
        for r in records
    ]


@router.patch("/tracking/{tracking_id}/status")
async def update_tracking_status(tracking_id: int, payload: dict, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(StatusTracking).where(StatusTracking.id == tracking_id))
    record = result.scalars().first()
    if not record:
        raise HTTPException(status_code=404, detail="Tracking record not found.")
    if "status" in payload:
        record.status = payload["status"]
    if "remarks" in payload:
        record.remarks = payload["remarks"]
    if "employee_id" in payload:
        record.employee_id = payload["employee_id"]
    await db.commit()
    return {"tracking_id": tracking_id, "status": record.status}


@router.get("/document-types")
async def list_document_types(db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(DocumentType))
    types = result.scalars().all()
    return [
        {
            "id": dt.id, "name": dt.name, "slug": dt.slug,
            "description": dt.description
        }
        for dt in types
    ]


@router.post("/document-types")
async def create_document_type(payload: DocumentTypeIn, db: AsyncSession = Depends(get_session)):
    dt = DocumentType(**payload.model_dump())
    db.add(dt)
    await db.commit()
    await db.refresh(dt)
    return {"id": dt.id, "name": dt.name, "slug": dt.slug}


@router.delete("/document-types/{dt_id}")
async def delete_document_type(dt_id: int, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(DocumentType).where(DocumentType.id == dt_id))
    dt = result.scalars().first()
    if not dt:
        raise HTTPException(status_code=404, detail="Document type not found.")
    await db.delete(dt)
    await db.commit()
    return {"deleted": dt_id}


@router.get("/requirements")
async def list_requirements(db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Requirement))
    reqs = result.scalars().all()
    out = []
    for r in reqs:
        await db.refresh(r, ["doc_type"])
        out.append({
            "id": r.id,
            "name": r.name,
            "ocr_mode": r.ocr_mode,
            "is_mandatory": r.is_mandatory,
            "document_type_id": r.document_type_id,
            "document_type_name": r.doc_type.name if r.doc_type else None,
            "document_type_slug": r.doc_type.slug if r.doc_type else None,
        })
    return out


@router.get("/requirements/by-type/{document_type_id}")
async def list_requirements_by_type(document_type_id: int, db: AsyncSession = Depends(get_session)):
    result = await db.execute(
        select(Requirement).where(Requirement.document_type_id == document_type_id)
    )
    reqs = result.scalars().all()
    return [
        {"id": r.id, "name": r.name, "ocr_mode": r.ocr_mode, "is_mandatory": r.is_mandatory}
        for r in reqs
    ]


@router.post("/requirements")
async def add_requirement(payload: RequirementIn, db: AsyncSession = Depends(get_session)):
    dt_result = await db.execute(select(DocumentType).where(DocumentType.id == payload.document_type_id))
    if not dt_result.scalars().first():
        raise HTTPException(status_code=404, detail="Document type not found.")
    req = Requirement(**payload.model_dump())
    db.add(req)
    await db.commit()
    await db.refresh(req)
    return {"id": req.id, "name": req.name}


@router.delete("/requirements/{req_id}")
async def delete_requirement(req_id: int, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Requirement).where(Requirement.id == req_id))
    req = result.scalars().first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found.")
    await db.delete(req)
    await db.commit()
    return {"deleted": req_id}
