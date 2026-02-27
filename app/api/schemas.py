from pydantic import BaseModel
from typing import Dict, Any, Optional

class SubmitRequest(BaseModel):
    aadhar_number: str
    document_request_type: str

class SubmitResponse(BaseModel):
    tracking_id: Optional[int] = None
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
    compliance_report: Optional[Dict[str, Any]] = None

class RequirementIn(BaseModel):
    name: str
    doc_type: str
    ocr_mode: str = "tesseract"
    description: Optional[str] = None
    is_mandatory: bool = True
