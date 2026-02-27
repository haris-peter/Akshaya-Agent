from typing import Dict, Any
from app.rules.eligibility_rules import get_scheme_rules

def requirement_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Requirement Agent (Policy Intelligence Agent)
    
    Inputs: scheme_id, citizen_profile (from state)
    Outputs: required_documents, scheme_rules (updates state)
    
    Responsibility: Determine the set of documents required for the citizen to apply.
    """
    print(f"Requirement Agent: Processing application for scheme {state.get('scheme_id')}...")
    
    scheme_id = state.get("scheme_id")
    rules = get_scheme_rules(scheme_id)
    
    if not rules:
        state["eligibility_result"] = {"status": "rejected", "reason": f"Scheme {scheme_id} not found or invalid."}
        state["progress_log"].append(f"Scheme validation failed.")
    else:
        state["scheme_rules"] = rules
        state["required_documents"] = rules.get("documents", [])
        state["progress_log"].append(f"Identified {len(state['required_documents'])} required documents.")
    
    return state
