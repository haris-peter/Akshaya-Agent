from typing import Dict, Any

async def eligibility_engine(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Eligibility Engine
    
    Inputs: citizen_profile, scheme_rules, missing_documents (from state)
    Outputs: eligibility_result (Approval/Rejection object) (updates state)
    
    Responsibility: Deterministic validation against rules. No LLM allowed.
    """
    print("Eligibility Engine: Validating rules...")
    
    # 1. Did we fail to collect all required documents?
    missing_docs = state.get("missing_documents", [])
    if missing_docs:
        state["eligibility_result"] = {
            "status": "rejected",
            "reason": f"Missing required documents: {', '.join(missing_docs)}"
        }
        state["progress_log"].append("Eligibility Check: Failed due to missing documents.")
        return state

    # 2. Extract profile and rules
    citizen = state.get("citizen_profile", {})
    rules = state.get("scheme_rules", {})
    
    income = citizen.get("annual_income")
    limit = rules.get("income_limit")
    
    # 3. Check income constraints deterministically
    if income is not None and limit is not None:
        if income > limit:
            state["eligibility_result"] = {
                "status": "rejected", 
                "reason": f"Annual income ({income}) exceeds scheme limit ({limit})."
            }
            state["progress_log"].append("Eligibility Check: Failed due to income limits.")
            return state

    # 4. If all checks pass, approve
    state["eligibility_result"] = {
        "status": "approved",
        "reason": "All criteria met."
    }
    state["progress_log"].append("Eligibility Check: Passed successfully.")
    
    return state
