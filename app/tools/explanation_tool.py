from typing import Dict, Any
from app.core.llm import get_llm
from app.core.retriever import get_relevant_policy_context, get_regulations_for_document_content
from app.tools.vault_tool import _get_requirement_summary_string
from langchain_core.prompts import PromptTemplate
import json


async def cross_check_vault_with_regulations(
    vault_summaries: Dict[str, Any],
    llm_requirement_summaries: Dict[str, str],
    requirements: list,
    scheme_id: str = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Cross-checks vault output against regulations/laws using the vector DB.
    For each requirement, uses the document content to retrieve relevant policy chunks,
    then assesses compliance. Returns the compliance report (output of the RAG cross-check).
    """
    llm = get_llm()
    compliance_report = {}

    for req in requirements:
        req_name = req["name"]
        summary_raw = llm_requirement_summaries.get(req_name) or vault_summaries.get(req_name)
        if isinstance(summary_raw, str):
            summary = summary_raw
        elif summary_raw:
            summary = _get_requirement_summary_string(summary_raw, req_name)
        else:
            summary = "NOT PROVIDED"
        if not summary or (isinstance(summary, str) and summary.strip() == ""):
            summary = "NOT PROVIDED"

        if summary == "NOT PROVIDED":
            compliance_report[req_name] = {
                "compliant": False,
                "status": "missing",
                "notes": "Document was not submitted."
            }
            continue

        policy_context = await get_regulations_for_document_content(
            document_content=summary,
            requirement_name=req_name,
            scheme_id=scheme_id,
            top_k=5,
        )

        template = """
        You are a government compliance officer reviewing a submitted document.

        Requirement: {req_name}
        Document Summary: {summary}

        Relevant Policy/Regulations:
        ---
        {policy_context}
        ---

        Based on the above, respond ONLY with a JSON:
        {{
            "compliant": true or false,
            "status": "compliant" | "review_needed" | "non_compliant",
            "notes": "brief explanation of compliance assessment"
        }}
        """
        prompt = PromptTemplate.from_template(template)
        chain = prompt | llm
        response = await chain.ainvoke({
            "req_name": req_name,
            "summary": summary,
            "policy_context": policy_context or "No specific regulations found."
        })

        try:
            parsed = json.loads(response.content)
        except Exception:
            content = response.content
            start = content.find("{")
            end = content.rfind("}") + 1
            try:
                parsed = json.loads(content[start:end])
            except Exception:
                parsed = {"compliant": True, "status": "review_needed", "notes": content}

        compliance_report[req_name] = parsed

    return compliance_report


async def explanation_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Uses vault response to cross-check each requirement against regulations/laws
    via the vector DB (RAG), then outputs the compliance report.
    """
    result = state.get("eligibility_result", {})
    reason = result.get("reason", "")
    scheme_id = state.get("scheme_id")
    vault_summaries = state.get("vault_summaries", {})
    requirements = state.get("requirements", [])
    llm_summaries = state.get("llm_requirement_summaries", {})

    print("Explanation Tool: Cross-checking vault response with regulations (vector DB)...")
    compliance_report = await cross_check_vault_with_regulations(
        vault_summaries=vault_summaries,
        llm_requirement_summaries=llm_summaries,
        requirements=requirements,
        scheme_id=scheme_id,
    )
    state["compliance_report"] = compliance_report

    if result.get("status") == "rejected":
        llm = get_llm()
        policy_context = await get_relevant_policy_context(query=reason, scheme_id=scheme_id)
        template = """
        You are Saarthi, a polite government AI assistant.
        A citizen's application was rejected.
        Rejection reason: {reason}

        Relevant policy excerpts:
        ---
        {policy_context}
        ---

        Explain the rejection clearly and politely in 2-3 sentences. Cite policy clauses if available.
        """
        prompt = PromptTemplate.from_template(template)
        chain = prompt | llm
        explanation_response = await chain.ainvoke({
            "reason": reason,
            "policy_context": policy_context or "No specific policy excerpt found."
        })
        state["eligibility_result"]["explanation"] = explanation_response.content

    state["progress_log"].append("Compliance assessment complete.")
    return state
