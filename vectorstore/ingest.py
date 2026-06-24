"""
vectorstore/ingest.py
Ingests coding standards documents into ChromaDB using sentence-transformers embeddings.
Run once to build the vector store: python -m vectorstore.ingest
"""

import os
import glob
from pathlib import Path
from dotenv import load_dotenv
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

load_dotenv()

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./vectorstore/chroma_db")
STANDARDS_DIR = "./data/coding_standards"
COLLECTION_NAME = "coding_standards"
CHUNK_SIZE = 500  # characters per chunk
CHUNK_OVERLAP = 50


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        # Try to break at a newline to avoid mid-sentence splits
        if end < len(text):
            last_newline = chunk.rfind("\n")
            if last_newline > chunk_size // 2:
                chunk = chunk[:last_newline]
                end = start + last_newline
        chunks.append(chunk.strip())
        start = end - overlap
    return [c for c in chunks if len(c) > 50]  # filter tiny chunks


def ingest_documents():
    """Load markdown files and ingest into ChromaDB."""
    print(f"Initializing ChromaDB at: {CHROMA_PERSIST_DIR}")
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

    # Use sentence-transformers — runs on CPU, no GPU needed
    embedding_fn = SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    # Get or create collection
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
        metadata={"description": "Coding standards and best practices"},
    )

    md_files = glob.glob(os.path.join(STANDARDS_DIR, "*.md"))
    if not md_files:
        print(f"No markdown files found in {STANDARDS_DIR}")
        return

    all_chunks = []
    all_ids = []
    all_metadata = []

    for filepath in md_files:
        filename = Path(filepath).stem
        print(f"Processing: {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        chunks = chunk_text(content)
        print(f"  → {len(chunks)} chunks created")

        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_ids.append(f"{filename}_chunk_{i}")
            all_metadata.append({"source": filename, "chunk_index": i})

    # Upsert into collection
    collection.upsert(
        documents=all_chunks,
        ids=all_ids,
        metadatas=all_metadata,
    )
    print(f"\n✅ Ingested {len(all_chunks)} chunks from {len(md_files)} files into ChromaDB.")
    print(f"Collection '{COLLECTION_NAME}' now has {collection.count()} documents.")


def query_standards(query: str, n_results: int = 3) -> list[dict]:
    """Query the vector store for relevant coding standards."""
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    embedding_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    collection = client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
    )
    results = collection.query(query_texts=[query], n_results=n_results)
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    return [{"content": doc, "source": meta["source"]} for doc, meta in zip(docs, metas)]


if __name__ == "__main__":
    ingest_documents()
