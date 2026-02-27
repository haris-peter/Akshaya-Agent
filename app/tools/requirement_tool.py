from typing import Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session
from app.db.models import Citizen, Scheme, Requirement

async def requirement_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Requirement Tool

    Loads scheme requirements from the Requirement table (admin-managed).
    Loads citizen profile from the Citizen table.
    Passes both into state for downstream tools.
    """
    citizen_id = state.get("citizen_id")
    scheme_id = state.get("scheme_id")

    print(f"Requirement Tool: Processing application {citizen_id} for scheme {scheme_id}...")

    async with async_session() as db:
        citizen_result = await db.execute(select(Citizen).where(Citizen.citizen_id == citizen_id))
        citizen = citizen_result.scalars().first()

        scheme_result = await db.execute(select(Scheme).where(Scheme.scheme_id == scheme_id))
        scheme = scheme_result.scalars().first()

        reqs_result = await db.execute(
            select(Requirement).where(Requirement.scheme_id == scheme_id)
        )
        requirements = reqs_result.scalars().all()

    if not citizen:
        state["eligibility_result"] = {"status": "error", "reason": f"Citizen {citizen_id} not found."}
        return state

    if not scheme:
        state["eligibility_result"] = {"status": "error", "reason": f"Scheme {scheme_id} not found."}
        return state

    from datetime import date
    dob = citizen.dob
    age = (date.today() - dob).days // 365 if dob else 0

    state["citizen_profile"] = {
        "citizen_id": citizen.citizen_id,
        "name": citizen.name,
        "annual_income": citizen.annual_income,
        "district": citizen.district,
        "age": age,
        "aadhar_number": citizen.aadhar_number,
    }

    state["scheme_rules"] = {
        "income_limit": scheme.income_limit,
        "district_required": scheme.district_required,
        "raw_db_name": scheme.name,
        "rules_json": scheme.rules_json or {}
    }

    state["requirements"] = [
        {
            "id": r.id,
            "name": r.name,
            "doc_type": r.doc_type,
            "ocr_mode": r.ocr_mode,
            "description": r.description,
            "is_mandatory": r.is_mandatory,
        }
        for r in requirements
    ]

    state["required_documents"] = [r.name for r in requirements if r.is_mandatory]
    state["progress_log"].append(f"Requirements loaded: {len(requirements)} item(s) for {scheme_id}.")

    return state
