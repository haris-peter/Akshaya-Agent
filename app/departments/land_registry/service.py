import uuid
from datetime import datetime, timezone
from app.departments.schemas import DocumentRequest, DocumentResponse

def generate_land_document(request: DocumentRequest) -> DocumentResponse:
    """
    Simulates the land registry.
    Valid document types: property_ownership, land_record
    """
    valid_docs = ["property_ownership", "land_record"]
    
    if request.document_type not in valid_docs:
        return DocumentResponse(
            status="error",
            message=f"Invalid document type. Allowed types: {', '.join(valid_docs)}"
        )
        
    doc_id = f"LND-{uuid.uuid4().hex[:8].upper()}"
    issued = datetime.now(timezone.utc).isoformat()
    
    return DocumentResponse(
        status="success",
        document_id=doc_id,
        issued_at=issued,
        hash_signature=f"hash_{doc_id}"
    )
