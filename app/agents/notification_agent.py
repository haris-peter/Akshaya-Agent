from typing import Dict, Any

def notification_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Notification Agent
    
    Outputs: Structured output / progress event (updates state / emits)
    
    Responsibility: Produces final structured output for citizen.
    """
    app_id = state.get("citizen_id", "Unknown")
    result = state.get("eligibility_result", {})
    
    print("\n" + "="*50)
    print(f"NOTIFICATION FOR CITIZEN: {app_id}")
    print("="*50)
    print(f"Status: {result.get('status', 'pending').upper()}")
    
    if result.get("status") == "rejected":
        print(f"Reason: {result.get('reason')}")
        print(f"Explanation: {result.get('explanation')}")
    else:
        print("Congratulations! Your application has been approved.")
        print(f"Generated Documents: {', '.join(state.get('collected_documents', []))}")
        
    print("="*50 + "\n")
    
    state["progress_log"].append("Final notification sent to citizen.")
    return state
