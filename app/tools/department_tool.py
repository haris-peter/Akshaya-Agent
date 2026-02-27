from typing import Dict, Any
import httpx

async def department_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Department Fetch Agent
    
    Inputs: citizen_id, missing_documents (from state)
    Outputs: Append to collected_documents, clear missing_documents (updates state)
    
    Responsibility: Interface with department agents to acquire missing documents via API.
    """
    citizen_id = state.get("citizen_id")
    missing_docs = state.get("missing_documents", [])
    collected_docs = state.get("collected_documents", [])
    
    if not missing_docs:
        return state
        
    print(f"Department Agent: Retrieving {len(missing_docs)} missing documents...")
    
    # In a real microservice architecture, these would route differently.
    # Here we mock hitting our own simulated department API
    async with httpx.AsyncClient() as client:
        newly_fetched = []
        still_missing = []
        
        for doc in missing_docs:
            state["progress_log"].append(f"Department Fetch: Requesting {doc}...")
            try:
                # We simulate calling the API gateway for department services
                response = await client.post(
                    "http://127.0.0.1:8000/api/v1/departments/generate", 
                    json={"citizen_id": citizen_id, "document_type": doc},
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    newly_fetched.append(data.get("document_type", doc))
                    state["progress_log"].append(f"Department Fetch: Successfully retrieved {doc}.")
                else:
                    still_missing.append(doc)
                    state["progress_log"].append(f"Department Fetch: Failed to get {doc}.")
            except Exception as e:
                still_missing.append(doc)
                state["progress_log"].append(f"Department Fetch: Error retrieving {doc} - {str(e)[:50]}")
                
        # Update the state collections
        state["collected_documents"].extend(newly_fetched)
        state["missing_documents"] = still_missing

    return state
