from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DocumentRequest(BaseModel):
    citizen_id: str
    document_type: str

class DocumentResponse(BaseModel):
    status: str
    document_id: Optional[str] = None
    issued_at: Optional[str] = None
    message: Optional[str] = None
    hash_signature: Optional[str] = None
