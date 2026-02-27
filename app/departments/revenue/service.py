import uuid
from datetime import datetime, timezone
from app.departments.schemas import DocumentRequest, DocumentResponse

# Dummy Database/Simulation Logic
def generate_revenue_document(request: DocumentRequest) -> DocumentResponse:
    """
    Simulates the revenue department.
    Valid document types: income_certificate, caste_certificate
    """
    valid_docs = ["income_certificate", "caste_certificate"]
    
    if request.document_type not in valid_docs:
        return DocumentResponse(
            status="error",
            message=f"Invalid document type. Allowed types: {', '.join(valid_docs)}"
        )
        
    doc_id = f"REV-{uuid.uuid4().hex[:8].upper()}"
    issued = datetime.now(timezone.utc).isoformat()
    
    return DocumentResponse(
        status="success",
        document_id=doc_id,
        issued_at=issued,
        hash_signature=f"hash_{doc_id}"
    )
