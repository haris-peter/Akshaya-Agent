import uuid
from datetime import datetime, timezone
from app.departments.schemas import DocumentRequest, DocumentResponse

def generate_tax_document(request: DocumentRequest) -> DocumentResponse:
    """
    Simulates the tax department.
    Valid document types: tax_clearance, pan_validation
    """
    valid_docs = ["tax_clearance", "pan_validation"]
    
    if request.document_type not in valid_docs:
        return DocumentResponse(
            status="error",
            message=f"Invalid document type. Allowed types: {', '.join(valid_docs)}"
        )
        
    doc_id = f"TAX-{uuid.uuid4().hex[:8].upper()}"
    issued = datetime.now(timezone.utc).isoformat()
    
    return DocumentResponse(
        status="success",
        document_id=doc_id,
        issued_at=issued,
        hash_signature=f"hash_{doc_id}"
    )
