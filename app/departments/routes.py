from fastapi import APIRouter, HTTPException
from app.departments.schemas import DocumentRequest, DocumentResponse
from app.departments.revenue.service import generate_revenue_document
from app.departments.tax.service import generate_tax_document
from app.departments.land_registry.service import generate_land_document

router = APIRouter()

@router.post("/revenue/generate-document", response_model=DocumentResponse)
async def revenue_api(request: DocumentRequest):
    response = generate_revenue_document(request)
    if response.status == "error":
        raise HTTPException(status_code=400, detail=response.message)
    return response

@router.post("/tax/generate-document", response_model=DocumentResponse)
async def tax_api(request: DocumentRequest):
    response = generate_tax_document(request)
    if response.status == "error":
        raise HTTPException(status_code=400, detail=response.message)
    return response

@router.post("/land/generate-document", response_model=DocumentResponse)
async def land_api(request: DocumentRequest):
    response = generate_land_document(request)
    if response.status == "error":
        raise HTTPException(status_code=400, detail=response.message)
    return response
