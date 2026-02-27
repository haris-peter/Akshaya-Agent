from typing import Dict, Any
from app.rules.engine import evaluate_rules

async def eligibility_engine(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Eligibility Engine

    Inputs: citizen_profile, scheme_rules, missing_documents (from state)
    Outputs: eligibility_result (Approval/Rejection object) (updates state)

    Responsibility: Generic deterministic rule evaluation. No LLM allowed.
    Reads rules_json from scheme_rules and evaluates them against citizen_profile.
    """
    print("Eligibility Engine: Validating rules...")

    # 1. Check all required documents are present
    missing_docs = state.get("missing_documents", [])
    if missing_docs:
        state["eligibility_result"] = {
            "status": "rejected",
            "reason": f"Missing required documents: {', '.join(missing_docs)}"
        }
        state["progress_log"].append("Eligibility Check: Failed due to missing documents.")
        return state

    # 2. Run JSON rules engine
    citizen = state.get("citizen_profile", {})
    rules_json = state.get("scheme_rules", {}).get("rules_json")

    if rules_json:
        passed, reason = evaluate_rules(citizen, rules_json)
        if not passed:
            state["eligibility_result"] = {"status": "rejected", "reason": reason}
            state["progress_log"].append(f"Eligibility Check: Failed rule — {reason}")
            return state
    else:
        # Fallback: simple income check if no JSON rules are defined
        income = citizen.get("annual_income")
        limit = state.get("scheme_rules", {}).get("income_limit")
        if income is not None and limit is not None and income > limit:
            state["eligibility_result"] = {
                "status": "rejected",
                "reason": f"Annual income ({income}) exceeds scheme limit ({limit})."
            }
            state["progress_log"].append("Eligibility Check: Failed income check (fallback).")
            return state

    # 3. All checks passed
    state["eligibility_result"] = {"status": "approved", "reason": "All criteria met."}
    state["progress_log"].append("Eligibility Check: Passed successfully.")
    return state
