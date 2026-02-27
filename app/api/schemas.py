from pydantic import BaseModel
from typing import Dict, Any

class ApplyRequest(BaseModel):
    citizen_id: str
    scheme_id: str
    
class ApplyResponse(BaseModel):
    application_id: str
    status: str
    message: str

class DocumentUploadRequest(BaseModel):
    citizen_id: str
    filename: str

class DocumentUploadResponse(BaseModel):
    upload_id: str
    presigned_url: str
    message: str

class OCRWebhookRequest(BaseModel):
    upload_id: str
    status: str
    ocr_text: str = None
    error_message: str = None

class OCRWebhookResponse(BaseModel):
    status: str
    message: str
