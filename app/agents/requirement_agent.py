from typing import Dict, Any
from sqlalchemy.future import select
from app.db.session import async_session
from app.db.models import Citizen, Scheme
from app.rules.eligibility_rules import get_scheme_rules

async def requirement_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Requirement Agent (Policy Intelligence Agent)
    
    Inputs: scheme_id, citizen_id (from state)
    Outputs: required_documents, scheme_rules, citizen profile (updates state)
    """
    scheme_id = state.get("scheme_id")
    citizen_id = state.get("citizen_id")
    print(f"Requirement Agent: Processing application {citizen_id} for scheme {scheme_id}...")
    
    async with async_session() as db:
        citizen_res = await db.execute(select(Citizen).where(Citizen.citizen_id == citizen_id))
        citizen = citizen_res.scalars().first()
        
        scheme_res = await db.execute(select(Scheme).where(Scheme.scheme_id == scheme_id))
        scheme = scheme_res.scalars().first()

    if not citizen or not scheme:
        state["eligibility_result"] = {"status": "rejected", "reason": f"Scheme {scheme_id} or Citizen {citizen_id} not found."}
        state["progress_log"].append("Validation failed at database lookup.")
        return state

    rules = get_scheme_rules(scheme_id)
    
    state["scheme_rules"] = {
        "income_limit": scheme.income_limit,
        "district_required": scheme.district_required,
        "raw_db_name": scheme.name,
        "rules_json": scheme.rules_json or {}
    }
    
    # Store citizen info for eligibility engine
    state["citizen_profile"] = {
        "annual_income": citizen.annual_income,
        "district": citizen.district,
        "name": citizen.name
    }
    
    state["required_documents"] = rules.get("documents", ["income_certificate", "Aadhar Card"])
    state["progress_log"].append(f"Identified {len(state['required_documents'])} required documents.")
    
    return state
