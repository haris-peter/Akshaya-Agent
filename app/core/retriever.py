from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from langchain_community.embeddings import HuggingFaceEmbeddings
from app.db.session import async_session

_embeddings_model = None

def get_embeddings_model():
    global _embeddings_model
    if _embeddings_model is None:
        _embeddings_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return _embeddings_model

MAX_QUERY_LENGTH = 2000


async def get_relevant_policy_context(query: str, scheme_id: str = None, top_k: int = 3) -> str:
    """
    Performs vector similarity search against the PolicyDocument table.
    Returns the concatenated top-k most relevant policy text chunks.
    scheme_id is used as doc_type filter (e.g. "ADMIN" for admin panel context).
    """
    model = get_embeddings_model()
    query_vector = model.embed_query(query)
    
    async with async_session() as db:
        if scheme_id:
            sql = text("""
                SELECT content
                FROM policy_document
                WHERE doc_type = :doc_type
                ORDER BY embedding <-> CAST(:qv AS vector)
                LIMIT :k
            """)
            result = await db.execute(sql, {"doc_type": scheme_id, "qv": str(query_vector), "k": top_k})
        else:
            sql = text("""
                SELECT content
                FROM policy_document
                ORDER BY embedding <-> CAST(:qv AS vector)
                LIMIT :k
            """)
            result = await db.execute(sql, {"qv": str(query_vector), "k": top_k})
        
        rows = result.fetchall()
    
    if not rows:
        return ""
    
    return "\n\n".join(row[0] for row in rows)


async def get_regulations_for_document_content(
    document_content: str,
    requirement_name: str,
    scheme_id: str = None,
    top_k: int = 5
) -> str:
    """
    Cross-checks document content against regulations by querying the vector DB
    with the actual document text. Returns relevant laws/regulations for RAG compliance.
    """
    if not document_content or not document_content.strip():
        return ""
    query = (requirement_name + " " + document_content.strip())[:MAX_QUERY_LENGTH]
    return await get_relevant_policy_context(query=query, scheme_id=scheme_id, top_k=top_k)
