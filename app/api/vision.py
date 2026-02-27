from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx
from app.db.session import get_session
from app.db.models import Document
from app.api.schemas import BlueprintAnalysisRequest, BlueprintVerificationResult
from app.core.bedrock import analyze_blueprint_image, analyze_blueprint_pdf

router = APIRouter()

@router.post("/analyze-blueprint", response_model=BlueprintVerificationResult)
async def analyze_blueprint(request: BlueprintAnalysisRequest, db: AsyncSession = Depends(get_session)):
    """
    Analyzes a blueprint document (Image or PDF) from an S3 URL using an Amazon Bedrock Vision Model
    and returns structured findings.
    """
    # 1. Fetch document from database
    result = await db.execute(select(Document).where(Document.id == request.document_id))
    doc = result.scalars().first()

    if not doc:
        raise HTTPException(status_code=404, detail=f"Document ID {request.document_id} not found.")

    if not doc.file_url:
        raise HTTPException(status_code=400, detail="Document does not have an uploaded file URL.")

    # 2. Fetch the actual file bytes from the URL
    async with httpx.AsyncClient() as client:
        response = await client.get(doc.file_url)
        if response.status_code != 200:
             raise HTTPException(status_code=500, detail="Failed to fetch document from storage.")
        file_bytes = response.content

    # 3. Determine if image or PDF based on extension/content type
    # For now, simplistic URL-based check
    is_pdf = doc.file_url.lower().endswith('.pdf') or response.headers.get("Content-Type", "").startswith("application/pdf")
    
    try:
        # 4. Invoke Bedrock Vision Model via Instructor
        if is_pdf:
            analysis_result = analyze_blueprint_pdf(file_bytes, request.prompt)
        else:
            # Assuming JPEG for default if not PDF, but Claude handles most image types natively
            content_type = response.headers.get("Content-Type", "image/jpeg")
            analysis_result = analyze_blueprint_image(file_bytes, request.prompt, content_type)
            
        return analysis_result

    except Exception as e:
        print(f"Bedrock Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze blueprint: {str(e)}")
