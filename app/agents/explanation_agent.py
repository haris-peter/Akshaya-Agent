from typing import Dict, Any
from app.core.llm import get_llm
from app.core.retriever import get_relevant_policy_context
from langchain_core.prompts import PromptTemplate

async def explanation_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Explanation Agent

    Inputs: eligibility_result.reason (from state)
    Outputs: Explanation string based on policy (updates state / progress log)

    Responsibility: Use RAG over policy documents to clarify why an application was rejected.
    """
    result = state.get("eligibility_result", {})
    reason = result.get("reason", "Unknown reason.")
    scheme_id = state.get("scheme_id")

    print(f"Explanation Agent: Generating explanation for rejection ({reason})...")

    llm = get_llm()

    # RAG: Retrieve relevant policy passages to back up the rejection reason
    policy_context = await get_relevant_policy_context(query=reason, scheme_id=scheme_id)

    template = """
    You are a polite government AI assistant named Saarthi.
    A citizen's application for a scheme was rejected.

    Here is the official system reason for rejection: {reason}

    Here are the relevant excerpts from the official scheme policy document:
    ---
    {policy_context}
    ---

    Using the policy excerpts above, explain the rejection clearly and politely to the citizen in 2-3 sentences.
    Cite the specific policy rule that led to the rejection if possible. Do not hallucinate any additional policies.
    """
    prompt = PromptTemplate.from_template(template)
    chain = prompt | llm

    explanation_response = await chain.ainvoke({"reason": reason, "policy_context": policy_context or "No specific policy excerpt found."})
    explanation = explanation_response.content

    state["eligibility_result"]["explanation"] = explanation
    state["progress_log"].append("RAG-backed rejection explanation generated.")

    return state
