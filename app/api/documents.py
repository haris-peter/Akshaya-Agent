import uuid
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.api.schemas import (
    DocumentUploadRequest,
    DocumentUploadResponse,
    OCRWebhookRequest,
    OCRWebhookResponse
)
from app.core.s3 import generate_presigned_upload_url
from app.db.database import get_db
from app.db.models import DocumentUpload

router = APIRouter()

@router.post("/upload-url", response_model=DocumentUploadResponse)
async def generate_upload_url(request: DocumentUploadRequest, db: Session = Depends(get_db)):
    """
    Generates an S3 presigned URL for the citizen to upload their document directly.
    Creates a pending record in the database to track the OCR process.
    """
    upload_id = f"UPL-{uuid.uuid4().hex[:8].upper()}"
    s3_key = f"documents/{request.citizen_id}/{upload_id}_{request.filename}"
    
    # Generate S3 URL
    presigned_url = generate_presigned_upload_url(s3_key)
    if not presigned_url:
        raise HTTPException(status_code=500, detail="Failed to generate S3 upload URL")

    # Create Tracking Record
    new_upload = DocumentUpload(
        upload_id=upload_id,
        citizen_id=request.citizen_id,
        s3_key=s3_key,
        status="pending"
    )
    db.add(new_upload)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database err: {str(e)}")

    return DocumentUploadResponse(
        upload_id=upload_id,
        presigned_url=presigned_url,
        message="Upload URL generated successfully, please use it to PUT your file."
    )

@router.post("/webhooks/ocr-complete", response_model=OCRWebhookResponse)
async def ocr_webhook(request: OCRWebhookRequest, db: Session = Depends(get_db)):
    """
    Webhook target for the asynchronous Tesseract OCR Lambda function.
    The Lambda invokes this endpoint once processing is complete (success or failure).
    """
    upload_record = db.query(DocumentUpload).filter(DocumentUpload.upload_id == request.upload_id).first()
    
    if not upload_record:
        raise HTTPException(status_code=404, detail="Upload record not found")

    upload_record.status = request.status
    if request.ocr_text:
        upload_record.ocr_text = request.ocr_text

    try:
        db.commit()
        # Optionally, this is where you could emit a WebSocket message to the client 
        # that their OCR processing has finished.
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return OCRWebhookResponse(
        status="success",
        message=f"Upload {request.upload_id} updated to {request.status}."
    )
