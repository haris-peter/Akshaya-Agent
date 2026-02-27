import json
import asyncio
import httpx
from typing import Dict, Any

from sqlalchemy import select
from app.db.session import async_session
from app.db.models import Document, Citizen

INTERNAL_API = "http://127.0.0.1:8000/api/v1/documents"
OCR_POLL_INTERVAL = 4
OCR_POLL_TIMEOUT  = 120


async def _poll_for_ocr(job_id: str) -> Dict:
    """
    Polls GET /documents/status/{job_id} until status is 'completed' or 'failed'.
    Returns the ocr_summary dict if completed, else an error dict.
    """
    elapsed = 0
    async with httpx.AsyncClient(timeout=10.0) as client:
        while elapsed < OCR_POLL_TIMEOUT:
            resp = await client.get(f"{INTERNAL_API}/status/{job_id}")
            if resp.status_code == 200:
                data = resp.json()
                if data["status"] == "completed":
                    return data.get("ocr_summary") or {}
                if data["status"] == "failed":
                    return {"error": f"OCR failed for job {job_id}"}
            await asyncio.sleep(OCR_POLL_INTERVAL)
            elapsed += OCR_POLL_INTERVAL
    return {"error": f"OCR timed out after {OCR_POLL_TIMEOUT}s for job {job_id}"}


async def vault_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Vault Tool

    For each requirement:
    1. Checks if a completed Document already exists for this citizen + requirement.
       → If yes: reuses the stored ocr_summary (shows 'already exists').
    2. If no completed document: uploads the file via POST /documents/upload
       which calls the real Tesseract Lambda and stores the job_id.
    3. Polls GET /documents/status/{job_id} until the OCR webhook fires.
    4. Collects all OCR summaries as vault_summaries for downstream RAG.

    State in:  aadhar_number, requirements, uploaded_files
    State out: vault_summaries {req_name: rag_json}, collected_documents, missing_documents
    """
    aadhar = state.get("aadhar_number", "")
    requirements = state.get("requirements", [])
    uploaded_files: Dict[str, bytes] = state.get("uploaded_files", {})

    vault_summaries = {}
    collected = []
    missing = []

    async with async_session() as db:
        citizen_result = await db.execute(
            select(Citizen).where(Citizen.aadhar_number == aadhar)
        )
        citizen = citizen_result.scalars().first()

    if not citizen:
        state["vault_summaries"] = {}
        state["progress_log"].append("Vault: Citizen not found.")
        return state

    for req in requirements:
        req_id   = req["id"]
        req_name = req["name"]

        state["progress_log"].append(f"Vault: Checking '{req_name}'...")

        async with async_session() as db:
            existing_result = await db.execute(
                select(Document).where(
                    Document.citizen_id == citizen.id,
                    Document.requirement_id == req_id,
                    Document.status == "completed"
                )
            )
            existing_doc = existing_result.scalars().first()

        if existing_doc and existing_doc.ocr_summary:
            vault_summaries[req_name] = json.loads(existing_doc.ocr_summary)
            collected.append(req_name)
            state["progress_log"].append(
                f"Vault: '{req_name}' already processed ✔  (reusing existing document)"
            )
            continue

        file_bytes = uploaded_files.get(req_name)
        if not file_bytes:
            missing.append(req_name)
            vault_summaries[req_name] = {"error": "NOT PROVIDED"}
            state["progress_log"].append(f"Vault: '{req_name}' not uploaded — skipped.")
            continue

        state["progress_log"].append(f"Vault: Uploading '{req_name}' to Tesseract Lambda...")

        async with httpx.AsyncClient(timeout=60.0) as client:
            upload_resp = await client.post(
                f"{INTERNAL_API}/upload",
                data={
                    "citizen_aadhar": aadhar,
                    "requirement_id": str(req_id)
                },
                files={"file": (f"{req_name}.pdf", file_bytes, "application/pdf")}
            )

        if upload_resp.status_code != 200:
            missing.append(req_name)
            vault_summaries[req_name] = {"error": f"Upload failed: {upload_resp.text[:120]}"}
            state["progress_log"].append(f"Vault: Upload failed for '{req_name}'.")
            continue

        upload_data = upload_resp.json()

        if upload_data.get("already_exists"):
            job_id = upload_data["job_id"]
        else:
            job_id = upload_data.get("job_id")

        state["progress_log"].append(f"Vault: '{req_name}' uploaded — job_id={job_id}. Waiting for OCR...")

        rag_json = await _poll_for_ocr(job_id)
        vault_summaries[req_name] = rag_json

        if "error" not in rag_json:
            collected.append(req_name)
            state["progress_log"].append(f"Vault: '{req_name}' OCR complete.")
        else:
            missing.append(req_name)
            state["progress_log"].append(f"Vault: '{req_name}' OCR error — {rag_json['error']}")

    state["vault_summaries"] = vault_summaries
    state["collected_documents"] = collected
    state["missing_documents"] = missing
    return state
