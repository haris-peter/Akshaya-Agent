from typing import Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session
from app.db.models import Citizen, Requirement, DocumentType


async def requirement_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Requirement Tool

    Loads requirements from the DB based on `document_request_type` (slug).
    Loads citizen profile by `aadhar_number`.
    Passes both into state for downstream tools.
    """
    aadhar_number = state.get("aadhar_number")
    document_request_type = state.get("document_request_type")

    print(f"Requirement Tool: Aadhar={aadhar_number}, doc_type={document_request_type}")

    async with async_session() as db:
        citizen_result = await db.execute(
            select(Citizen).where(Citizen.aadhar_number == aadhar_number)
        )
        citizen = citizen_result.scalars().first()

        if not citizen:
            state["status"] = "error"
            state["progress_log"].append(f"Citizen with Aadhar {aadhar_number} not found.")
            return state

        dt_result = await db.execute(
            select(DocumentType).where(DocumentType.slug == document_request_type)
        )
        doc_type = dt_result.scalars().first()

        requirements = []
        if doc_type:
            reqs_result = await db.execute(
                select(Requirement).where(Requirement.document_type_id == doc_type.id)
            )
            requirements = reqs_result.scalars().all()

    state["citizen"] = {
        "id": citizen.id,
        "name": citizen.name,
        "aadhar_number": citizen.aadhar_number,
        "phone": citizen.phone,
        "email": citizen.email,
        "address": citizen.address,
        "district": citizen.district,
    }

    state["requirements"] = [
        {
            "id": r.id,
            "name": r.name,
            "ocr_mode": r.ocr_mode,
            "doc_type": document_request_type,
            "is_mandatory": r.is_mandatory,
        }
        for r in requirements
    ]

    state["required_documents"] = [r.name for r in requirements if r.is_mandatory]
    state["progress_log"].append(
        f"Requirements loaded: {len(requirements)} item(s) for '{document_request_type}'."
    )

    return state
