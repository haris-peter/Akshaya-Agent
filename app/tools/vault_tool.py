import json
import asyncio
import httpx
from typing import Dict, Any

from sqlalchemy import select
from app.db.session import async_session
from app.db.models import Document, Citizen

INTERNAL_API = "http://127.0.0.1:8000/api/v1/documents"
OCR_POLL_INTERVAL = 4
OCR_POLL_TIMEOUT = 120


def _blueprint_result_to_rag_json(requirement_name: str, doc_type_slug: str, result: Any) -> Dict:
    """Convert Bedrock BlueprintVerificationResult to same shape as _build_rag_json for RAG."""
    parts = [
        result.overall_conclusion or "",
        f"Dimensions: {result.dimensions_found}" if result.dimensions_found else "",
        "Components: " + ", ".join(result.structural_components_found) if result.structural_components_found else "",
        "Issues: " + ", ".join(result.compliance_issues) if result.compliance_issues else "",
    ]
    raw_text = "\n".join(p for p in parts if p).strip()
    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
    return {
        requirement_name: {
            "doc_type": doc_type_slug,
            "raw_text": raw_text,
            "summary_lines": lines[:30],
            "char_count": len(raw_text),
        }
    }


def _get_requirement_summary_string(vault_entry: Dict, req_name: str) -> str:
    """Extract a single summary string for LLM from vault_summaries[req_name]."""
    if isinstance(vault_entry, str):
        return vault_entry
    if vault_entry.get("error"):
        return f"Error: {vault_entry.get('error', 'Unknown')}"
    inner = vault_entry.get(req_name) if isinstance(vault_entry.get(req_name), dict) else vault_entry
    if not inner:
        inner = vault_entry
    raw = inner.get("raw_text") if isinstance(inner, dict) else ""
    if raw:
        return raw
    lines = inner.get("summary_lines", []) if isinstance(inner, dict) else []
    return "\n".join(lines) if lines else str(inner)


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

        ocr_mode = req.get("ocr_mode", "tesseract")
        dt = req.get("doc_type")
        doc_type_slug = (getattr(dt, "slug", None) if dt is not None else None) or (dt.get("slug") if isinstance(dt, dict) else None) or ""

        if ocr_mode == "llm_vision":
            state["progress_log"].append(f"Vault: Extracting '{req_name}' via Bedrock vision...")
            try:
                from app.core.bedrock import analyze_blueprint_pdf, analyze_blueprint_image
                prompt = "Extract key information: dimensions, structural components, and any compliance issues."
                if file_bytes[:4] == b"%PDF":
                    blueprint_result = analyze_blueprint_pdf(file_bytes, prompt)
                else:
                    blueprint_result = analyze_blueprint_image(file_bytes, prompt)
                rag_json = _blueprint_result_to_rag_json(req_name, doc_type_slug or "blueprint", blueprint_result)
                vault_summaries[req_name] = rag_json
                collected.append(req_name)
                state["progress_log"].append(f"Vault: '{req_name}' Bedrock extraction complete.")
            except Exception as e:
                vault_summaries[req_name] = {"error": str(e)}
                missing.append(req_name)
                state["progress_log"].append(f"Vault: '{req_name}' Bedrock error — {e}")
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
    state["llm_requirement_summaries"] = {
        req_name: _get_requirement_summary_string(vault_summaries.get(req_name, {}), req_name)
        for req_name in vault_summaries
    }
    return state
