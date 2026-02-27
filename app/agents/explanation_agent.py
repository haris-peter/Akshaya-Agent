from typing import Dict, Any

def explanation_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Explanation Agent
    
    Inputs: eligibility_result.reason (from state)
    Outputs: Explanation string based on policy (updates state / progress log)
    
    Responsibility: Use RAG over policy documents to clarify why an application was rejected.
    """
    # TODO: Implement RAG query logic for rejected applications
    print("Explanation Agent: Generating explanation for eligibility result...")
    return state
