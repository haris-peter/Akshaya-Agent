from typing import Dict, Any
from app.core.llm import get_llm
from langchain_core.prompts import PromptTemplate

def explanation_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Explanation Agent
    
    Inputs: eligibility_result.reason (from state)
    Outputs: Explanation string based on policy (updates state / progress log)
    
    Responsibility: Use RAG over policy documents to clarify why an application was rejected.
    """
    result = state.get("eligibility_result", {})
    reason = result.get("reason", "Unknown reason.")
    
    print(f"Explanation Agent: Generating explanation for rejection ({reason})...")
    
    # Intialize LLM
    llm = get_llm()
    
    # For now, without a fully populated PGVector Store we do a static prompt. 
    # Later this will be a RetrieverQA chain.
    template = """
    You are a polite government AI assistant named Saarthi.
    A citizen's application for a scheme was rejected.
    Here is the official system reason for rejection: {reason}
    
    Explain this clearly and politely to the user in 2-3 sentences. Do not hallucinate extra policies.
    """
    prompt = PromptTemplate.from_template(template)
    chain = prompt | llm
    
    explanation = chain.invoke({"reason": reason}).content
    
    # Store the explanation in the result
    state["eligibility_result"]["explanation"] = explanation
    state["progress_log"].append("Rejection explanation generated.")
    
    return state
