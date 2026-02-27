from pydantic import BaseModel
from typing import Dict, Any

class ApplyRequest(BaseModel):
    citizen_id: str
    scheme_id: str
    
class ApplyResponse(BaseModel):
    application_id: str
    status: str
    message: str
