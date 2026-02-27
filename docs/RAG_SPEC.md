# `/docs/RAG_SPEC.md`

## 1. What Documents are Ingested
- Official government scheme PDFs
- Policy notifications

## 2. Embedding Model
- OpenAI embeddings or local Ollama embeddings

## 3. Chunking Strategy
- `RecursiveCharacterTextSplitter`

## 4. Vector DB
- `PGVector`

## 5. Retrieval Protocol
RAG is used ONLY for:
- Justifying rejection
- Explaining document requirements
- Answering citizen queries

RAG must not:
- Decide eligibility
- Modify rule outcomes
- Generate new rule interpretations

Example logic:
```python
def explain_rejection(reason):
    docs = retriever.get_relevant_documents(reason)
    return llm.invoke(docs + reason)
```
