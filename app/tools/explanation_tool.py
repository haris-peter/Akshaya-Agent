from typing import Dict, Any
from app.core.llm import get_llm
from app.core.retriever import get_relevant_policy_context
from langchain_core.prompts import PromptTemplate
import json

async def explanation_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Explanation & Compliance Assessment Tool

    Inputs: vault_summaries, requirements, eligibility_result (from state)
    Outputs: compliance_report — per-requirement RAG assessment + explanation

    Two responsibilities:
    1. If application is rejected: generate a polite rejection explanation backed by RAG policy.
    2. For each requirement in vault_summaries: assess compliance against regulations via RAG.
    """
    result = state.get("eligibility_result", {})
    reason = result.get("reason", "")
    scheme_id = state.get("scheme_id")
    vault_summaries = state.get("vault_summaries", {})
    requirements = state.get("requirements", [])
    compliance_report = {}

    print(f"Explanation Tool: Running RAG compliance assessment...")

    llm = get_llm()

    # 1. Per-requirement compliance assessment via RAG
    for req in requirements:
        req_name = req["name"]
        summary = vault_summaries.get(req_name, "NOT PROVIDED")

        if summary == "NOT PROVIDED":
            compliance_report[req_name] = {
                "compliant": False,
                "status": "missing",
                "notes": "Document was not submitted."
            }
            continue

        policy_context = await get_relevant_policy_context(
            query=f"{req_name} requirements regulations",
            scheme_id=scheme_id
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

    state["compliance_report"] = compliance_report

    # 2. If rejected: generate a polite explanation with policy context
    if result.get("status") == "rejected":
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
