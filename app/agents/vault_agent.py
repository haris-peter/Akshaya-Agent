from typing import Dict, Any

# Mock check - in a real app query DocumentVault
def check_document_vault(citizen_id: str, document_type: str) -> bool:
    """Mock checking if a citizen has a valid document of the required type."""
    # Assume citizen 123 has income_certificate but not caste_certificate
    mock_vault = {
        "123": ["income_certificate", "pan_validation"]
    }
    return document_type in mock_vault.get(citizen_id, [])

def vault_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Document Vault Agent
    
    Inputs: citizen_id, required_documents (from state)
    Outputs: collected_documents, missing_documents (updates state)
    
    Responsibility: Check existing citizen documents for validity in the vault.
    """
    citizen_id = state.get("citizen_id")
    required = state.get("required_documents", [])
    
    collected = []
    missing = []
    
    for doc in required:
        if check_document_vault(citizen_id, doc):
            collected.append(doc)
            state["progress_log"].append(f"Found {doc} in Document Vault.")
        else:
            missing.append(doc)
            state["progress_log"].append(f"Document missing: {doc}.")
            
    state["collected_documents"] = collected
    state["missing_documents"] = missing
    
    return state
