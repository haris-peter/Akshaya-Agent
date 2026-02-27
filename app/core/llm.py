from langchain_openai import ChatOpenAI
from app.core.config import settings

def get_llm():
    """
    Returns a configured LangChain ChatOpenAI instance 
    pointing to OpenRouter to use Mistral 7B (or whichever model is configured).
    """
    return ChatOpenAI(
        model=settings.LLM_MODEL,
        api_key=settings.OPENROUTER_API_KEY,
        openai_api_base="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "SaarthiAI",
        }
    )
