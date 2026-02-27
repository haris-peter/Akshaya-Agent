from fastapi import APIRouter, HTTPException
import uuid

from app.api.schemas import ApplyRequest, ApplyResponse
from app.graph.workflow import app_workflow

router = APIRouter()

@router.post("/apply", response_model=ApplyResponse)
async def submit_application(request: ApplyRequest):
    """
    Submits an application for a scheme and triggers the LangGraph Orchestrator.
    """
    application_id = f"APP-{uuid.uuid4().hex[:8].upper()}"
    
    # Initialize the LangGraph ApplicationState
    initial_state = {
        "citizen_id": request.citizen_id,
        "scheme_id": request.scheme_id,
        "scheme_rules": {},
        "required_documents": [],
        "collected_documents": [],
        "missing_documents": [],
        "eligibility_result": {},
        "progress_log": [f"Application {application_id} started"]
    }
    
    # In a real environment we would dispatch this to a task queue. 
    # For now, we invoke the LangGraph sync for demonstration.
    try:
        final_state = app_workflow.invoke(initial_state)
        # Assuming notification puts a status message
        
        return ApplyResponse(
            application_id=application_id,
            status="completed" if final_state.get("eligibility_result", {}).get("status") == "approved" else "rejected",
            message="Workflow completed"
        )
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))
