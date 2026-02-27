import base64
from typing import Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session
from app.db.models import Requirement, DocumentVault

async def _analyze_with_tesseract(file_bytes: bytes, requirement: Dict) -> str:
    """
    Tesseract OCR mode: extracts text from scanned images/PDFs.
    TODO: Replace this stub with a real Tesseract API call.
    API_URL = os.environ.get("TESSERACT_API_URL", "http://tesseract-service/ocr")
    """
    return f"[Tesseract OCR Stub] Text extracted for '{requirement['name']}'. Replace with real OCR API."

async def _analyze_with_llm_vision(file_bytes: bytes, requirement: Dict, citizen_id: str) -> str:
    """
    LLM Vision mode: uses Gemini vision to analyze blueprint/image documents.
    Sends the image to OpenRouter with vision model and returns a structured summary.
    """
    import httpx
    import os
    import json

    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    image_b64 = base64.b64encode(file_bytes).decode("utf-8")

    prompt = f"""
    You are analyzing a document submitted for government scheme verification.
    Document Type: {requirement['doc_type']}
    Requirement: {requirement['name']}
    Description: {requirement.get('description', '')}

    Analyze this image carefully and provide a JSON summary:
    {{
        "document_type": "{requirement['name']}",
        "key_findings": ["list key observations"],
        "measurements": {{}},
        "identifies_citizen": true/false,
        "summary": "one paragraph summary of what this document contains and its relevance"
    }}
    """

    payload = {
        "model": "google/gemini-2.0-flash-exp:free",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                ]
            }
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload
            )
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            try:
                parsed = json.loads(content)
                return parsed.get("summary", content)
            except Exception:
                return content
    except Exception as e:
        return f"[Vision LLM Error] {str(e)[:100]}"


async def vault_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Vault Tool

    Inputs: citizen_id, requirements (from state), uploaded_files (from state)
    Outputs: vault_summaries — {requirement_name: "text summary"}

    Modes per requirement:
      - ocr_mode="tesseract"  -> calls Tesseract OCR (stub)
      - ocr_mode="llm_vision" -> calls Gemini Vision LLM
    """
    citizen_id = state.get("citizen_id")
    requirements = state.get("requirements", [])
    uploaded_files = state.get("uploaded_files", {})
    vault_summaries = {}
    collected = []
    missing = []

    print(f"Vault Tool: Processing {len(requirements)} requirement(s) for citizen {citizen_id}...")

    async with async_session() as db:
        vault_result = await db.execute(
            select(DocumentVault).where(DocumentVault.citizen_id == citizen_id)
        )
        existing_docs = {doc.document_type: doc for doc in vault_result.scalars().all()}

    for req in requirements:
        req_name = req["name"]
        doc_type = req["doc_type"]
        ocr_mode = req.get("ocr_mode", "tesseract")

        state["progress_log"].append(f"Vault: Checking '{req_name}'...")

        # Check if document exists in the vault already
        if doc_type in existing_docs:
            vault_summaries[req_name] = f"Document on file: {doc_type} (valid until {existing_docs[doc_type].valid_until})"
            collected.append(req_name)
            continue

        # Check if uploaded in this session
        file_bytes = uploaded_files.get(req_name)
        if file_bytes:
            if ocr_mode == "llm_vision":
                summary = await _analyze_with_llm_vision(file_bytes, req, citizen_id)
            else:
                summary = await _analyze_with_tesseract(file_bytes, req)

            vault_summaries[req_name] = summary
            collected.append(req_name)
            state["progress_log"].append(f"Vault: '{req_name}' analyzed via {ocr_mode}.")
        else:
            missing.append(req_name)
            vault_summaries[req_name] = "NOT PROVIDED"
            state["progress_log"].append(f"Vault: '{req_name}' is missing.")

    state["vault_summaries"] = vault_summaries
    state["collected_documents"] = collected
    state["missing_documents"] = missing

    return state
