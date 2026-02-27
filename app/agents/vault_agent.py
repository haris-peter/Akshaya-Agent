from typing import Dict, Any
from sqlalchemy.future import select
from app.db.session import async_session
from app.db.models import DocumentVault

async def vault_agent(state: Dict[str, Any]) -> Dict[str, Any]:
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
    
    # Query Database for Citizen Documents
    async with async_session() as db:
        result = await db.execute(select(DocumentVault).where(DocumentVault.citizen_id == citizen_id))
        citizen_docs = result.scalars().all()
        
    citizen_doc_types = [doc.document_type for doc in citizen_docs]
    
    for doc_req in required:
        if doc_req in citizen_doc_types:
            collected.append(doc_req)
            state["progress_log"].append(f"Found {doc_req} in Document Vault.")
        else:
            missing.append(doc_req)
            state["progress_log"].append(f"Document missing: {doc_req}.")
            
    state["collected_documents"] = collected
    state["missing_documents"] = missing
    
    return state
