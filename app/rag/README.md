# `app/rag/`

This folder handles:
- PDF ingestion
- Embeddings
- Vector store connection
- Retrieval logic

You keep AI isolated here.
RAG must never decide eligibility; it is only used for explanation and querying policy clauses.
