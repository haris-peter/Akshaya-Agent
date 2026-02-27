import asyncio
import sys
import json
import os
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import engine, init_db
from app.db.models import PolicyDocument

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

POLICIES_DIR = Path(__file__).parent / "policies"
BATCH_SIZE = 50

def sanitize_text(text: str) -> str:
    """Remove null bytes and other problematic characters for PostgreSQL UTF-8."""
    return text.replace("\x00", "").strip()

def load_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")

def load_pdf_file(path: Path) -> str:
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages:
            txt = page.extract_text()
            if txt:
                pages.append(sanitize_text(txt))
        return "\n".join(pages)
    except ImportError:
        print(f"  [WARNING] pypdf not installed. Skipping {path.name}. Run: pip install pypdf")
        return ""

def load_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in (".txt", ".md"):
        return sanitize_text(load_text_file(path))
    elif suffix == ".pdf":
        return load_pdf_file(path)
    else:
        print(f"  [SKIP] Unsupported file type: {path.name}")
        return ""

async def setup_vector_extension():
    async with engine.begin() as conn:
        print("Ensuring pgvector extension is installed...")
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

async def ingest_file(embeddings_model, text_splitter, path: Path):
    print(f"\n  Processing: {path.name}")
    content = load_file(path)

    if not content.strip():
        print(f"  [SKIP] Empty or unreadable: {path.name}")
        return 0

    raw_stem = path.stem.upper()
    scheme_id = raw_stem.split("_")[0] if "_" in raw_stem else None

    chunks = text_splitter.split_text(content)
    # Sanitize each chunk individually
    chunks = [sanitize_text(c) for c in chunks if sanitize_text(c)]
    
    total = 0
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        vectors = embeddings_model.embed_documents(batch)
        
        async with AsyncSession(engine) as session:
            for idx, chunk in enumerate(batch):
                doc = PolicyDocument(
                    scheme_id=scheme_id,
                    content=chunk,
                    embedding=vectors[idx],
                    metadata_json=json.dumps({"source": path.name, "chunk": i + idx})
                )
                session.add(doc)
            await session.commit()
        
        total += len(batch)
        print(f"    Committed batch {i // BATCH_SIZE + 1}: {total}/{len(chunks)} chunks")

    print(f"  Done: {total} chunks from {path.name} (scheme_id={scheme_id})")
    return total

async def main():
    if not POLICIES_DIR.exists():
        print(f"Policies directory not found: {POLICIES_DIR}")
        sys.exit(1)

    policy_files = [
        f for f in POLICIES_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in (".txt", ".pdf", ".md") and f.name != ".gitkeep"
    ]

    if not policy_files:
        print(f"No policy documents found in '{POLICIES_DIR}'.")
        print("Add .txt, .md, or .pdf files to the 'policies/' folder and re-run.")
        sys.exit(0)

    print(f"Found {len(policy_files)} file(s) to ingest: {[f.name for f in policy_files]}")

    await setup_vector_extension()
    await init_db()

    print("\nLoading HuggingFace Embedding Model (all-MiniLM-L6-v2)...")
    embeddings_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=40,
        length_function=len,
    )

    total_chunks = 0
    for path in policy_files:
        total_chunks += await ingest_file(embeddings_model, text_splitter, path)

    print(f"\nIngestion complete! Total chunks stored: {total_chunks}")

if __name__ == "__main__":
    asyncio.run(main())
