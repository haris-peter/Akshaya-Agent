import base64
import asyncio
import uuid
from typing import Dict, Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session
from app.db.models import DocumentUpload

INTERNAL_API = "http://127.0.0.1:8000/api/v1/documents"
OCR_POLL_INTERVAL = 3    # seconds between status checks
OCR_POLL_TIMEOUT  = 120  # max seconds to wait for OCR webhook


async def _tesseract_webhook_flow(file_bytes: bytes, requirement: Dict, citizen_aadhar: str) -> str:
    """
    Webhook-based Tesseract OCR flow:
    1. Creates a DocumentUpload record via POST /documents/upload-url
    2. In production, client PUTs the file to S3; Tesseract Lambda processes it
       and calls POST /documents/webhooks/ocr-complete
    3. Here (since S3 isn't configured yet), we simulate completion by writing
       the OCR result directly to the DB, then poll the status endpoint.
    Returns: OCR text string
    """
    filename = f"{requirement['doc_type']}_{uuid.uuid4().hex[:6]}.jpg"

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{INTERNAL_API}/upload-url",
            json={"citizen_id": citizen_aadhar, "filename": filename}
        )
        if resp.status_code != 200:
            return f"[OCR Error] Failed to create upload record: {resp.text[:80]}"
        upload_data = resp.json()
        upload_id = upload_data["upload_id"]

    # --- STUB: Simulate Tesseract OCR callback ---
    # When the actual Tesseract Lambda is connected, remove this block.
    # The Lambda will PUT the file to S3 → process → call /webhooks/ocr-complete itself.
    stub_ocr_text = (
        f"[Tesseract Stub] OCR text extracted for '{requirement['name']}'. "
        f"File: {filename}. "
        f"Replace stub by configuring TESSERACT_LAMBDA_URL and S3_BUCKET_NAME in .env."
    )
    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.post(
            f"{INTERNAL_API}/webhooks/ocr-complete",
            json={"upload_id": upload_id, "status": "completed", "ocr_text": stub_ocr_text}
        )
    # --- END STUB ---

    # Poll status endpoint until OCR completes (or timeout)
    elapsed = 0
    async with httpx.AsyncClient(timeout=10.0) as client:
        while elapsed < OCR_POLL_TIMEOUT:
            poll = await client.get(f"{INTERNAL_API}/{upload_id}/status")
            if poll.status_code == 200:
                data = poll.json()
                if data["status"] == "completed":
                    return data.get("ocr_text") or "[OCR completed but no text returned]"
                if data["status"] == "failed":
                    return f"[OCR Failed] Tesseract could not process '{requirement['name']}'."
            await asyncio.sleep(OCR_POLL_INTERVAL)
            elapsed += OCR_POLL_INTERVAL

    return f"[OCR Timeout] Tesseract did not respond within {OCR_POLL_TIMEOUT}s for '{requirement['name']}'."


async def _analyze_with_llm_vision(file_bytes: bytes, requirement: Dict) -> str:
    """
    LLM Vision mode: sends the image to Gemini via OpenRouter.
    Used for blueprints, medical scans, or any image requiring semantic understanding.
    """
    import json
    import os

    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    image_b64 = base64.b64encode(file_bytes).decode("utf-8")

    prompt = f"""
    You are analyzing a government document for scheme verification.
    Document Type: {requirement['doc_type']}
    Requirement: {requirement['name']}
    Description: {requirement.get('description', '')}

    Analyze this image carefully. Respond ONLY with a JSON:
    {{
        "document_type": "{requirement['name']}",
        "key_findings": ["list of key observations"],
        "measurements": {{}},
        "summary": "one paragraph summary of document content and relevance"
    }}
    """

    payload = {
        "model": "google/gemini-2.0-flash-exp:free",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
            ]
        }]
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

    Processes each requirement using its configured analysis mode:
      - ocr_mode="tesseract"  → webhook-based OCR flow (via DocumentUpload + polling)
      - ocr_mode="llm_vision" → Gemini Vision LLM for blueprints/images

    Outputs:
      - vault_summaries: {requirement_name: "text summary"}
      - collected_documents: list of processed requirement names
      - missing_documents: list of unsubmitted requirement names
    """
    citizen_aadhar = state.get("aadhar_number", "unknown")
    requirements = state.get("requirements", [])
    uploaded_files = state.get("uploaded_files", {})
    vault_summaries = {}
    collected = []
    missing = []

    print(f"Vault Tool: Processing {len(requirements)} requirement(s) for Aadhar {citizen_aadhar}...")

    for req in requirements:
        req_name = req["name"]
        ocr_mode = req.get("ocr_mode", "tesseract")

        state["progress_log"].append(f"Vault: Processing '{req_name}' via {ocr_mode}...")

        file_bytes = uploaded_files.get(req_name)

        if file_bytes:
            if ocr_mode == "llm_vision":
                summary = await _analyze_with_llm_vision(file_bytes, req)
            else:
                summary = await _tesseract_webhook_flow(file_bytes, req, citizen_aadhar)

            vault_summaries[req_name] = summary
            collected.append(req_name)
            state["progress_log"].append(f"Vault: '{req_name}' analyzed.")
        else:
            missing.append(req_name)
            vault_summaries[req_name] = "NOT PROVIDED"
            state["progress_log"].append(f"Vault: '{req_name}' not uploaded — skipped.")

    state["vault_summaries"] = vault_summaries
    state["collected_documents"] = collected
    state["missing_documents"] = missing

    return state
