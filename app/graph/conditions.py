from app.graph.state import ApplicationState

def should_fetch_documents(state: ApplicationState) -> str:
    """
    Branching logic to decide what to do after checking the vault.
    
    If there are missing documents, we must fetch them from the departments.
    If all documents are collected, we can proceed to the eligibility engine.
    """
    if len(state.get("missing_documents", [])) > 0:
        return "fetch"
    return "eligible"

def check_eligibility_status(state: ApplicationState) -> str:
    """
    Branching logic to decide what to do after the eligibility engine runs.
    
    If the application is rejected, go to the explanation agent for RAG reasoning.
    If it is approved, go directly to the notification agent.
    """
    result = state.get("eligibility_result", {})
    if result.get("status") == "rejected":
        return "rejected"
    return "approved"
