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
    document_type_id: int
    name: str
    ocr_mode: str = "tesseract"
    is_mandatory: bool = True

class DocumentTypeIn(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None

class BlueprintVerificationResult(BaseModel):
    is_blueprint_valid: bool
    dimensions_found: Optional[str] = None
    structural_components_found: list[str] = []
    compliance_issues: list[str] = []
    overall_conclusion: str
    confidence_score: float

class BlueprintAnalysisRequest(BaseModel):
    document_id: int
    prompt: Optional[str] = "Analyze this blueprint and verify if it matches standard structural requirements."

