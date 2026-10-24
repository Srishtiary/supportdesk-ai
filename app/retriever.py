"""Knowledge base retriever using ChromaDB and Gemini embeddings."""

from pathlib import Path
from typing import Any

import chromadb

from app.llm import embed

# Paths for knowledge base and ChromaDB vector store
KB_DIR = Path("data/kb")
CHROMA_DIR = Path("chroma_store")
COLLECTION_NAME = "voltkart_kb"


def chunk_article(file_path: Path | str) -> list[dict[str, str]]:
    """Split a markdown file into chunks by '## ' section headings."""
    path = Path(file_path)
    content = path.read_text(encoding="utf-8")
    filename = path.name

    # Extract the main document title from the '# ' line
    doc_title = ""
    for line in content.splitlines():
        if line.startswith("# "):
            doc_title = line.replace("# ", "").strip()
            break

    # Split the article content by '## ' headings
    sections = content.split("\n## ")
    chunks: list[dict[str, str]] = []

    # Skip section 0 (which contains the # title and intro before the first ##)
    for section in sections[1:]:
        lines = section.splitlines()
        if not lines:
            continue

        heading = lines[0].strip()
        body = "\n".join(lines[1:]).strip()
        chunk_id = f"{filename}#{heading}"

        # Combine title, heading, and body for rich semantic representation
        chunk_text = f"{doc_title}\n## {heading}\n\n{body}".strip()

        chunks.append({
            "id": chunk_id,
            "filename": filename,
            "heading": heading,
            "text": chunk_text,
        })

    return chunks


def get_chroma_client(persist_directory: Path | str = CHROMA_DIR) -> chromadb.ClientAPI:
    """Return a persistent ChromaDB client pointing to the storage folder."""
    return chromadb.PersistentClient(path=str(persist_directory))


def index_kb(
    kb_directory: Path | str = KB_DIR,
    persist_directory: Path | str = CHROMA_DIR,
    force_reindex: bool = False,
) -> int:
    """Read all KB articles, chunk them, embed them, and save into ChromaDB."""
    kb_path = Path(kb_directory)
    client = get_chroma_client(persist_directory)

    # Use cosine distance for comparing vector angles
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    # Return existing chunk count if already indexed and not forcing reindex
    if not force_reindex and collection.count() > 0:
        return collection.count()

    all_chunks: list[dict[str, str]] = []
    for file_path in sorted(kb_path.glob("*.md")):
        all_chunks.extend(chunk_article(file_path))

    if not all_chunks:
        return 0

    ids = [chunk["id"] for chunk in all_chunks]
    texts = [chunk["text"] for chunk in all_chunks]
    metadatas = [
        {"filename": chunk["filename"], "heading": chunk["heading"]}
        for chunk in all_chunks
    ]

    # Embed chunks in batches of 25 to avoid large single requests
    batch_size = 25
    all_embeddings: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i : i + batch_size]
        batch_embeddings = embed(batch_texts)
        all_embeddings.extend(batch_embeddings)

    # Store chunks into ChromaDB
    collection.upsert(
        ids=ids,
        documents=texts,
        embeddings=all_embeddings,
        metadatas=metadatas,
    )

    return len(ids)


def search(
    query: str,
    k: int = 4,
    persist_directory: Path | str = CHROMA_DIR,
) -> list[dict[str, Any]]:
    """Search ChromaDB for the top k chunks most relevant to the query."""
    client = get_chroma_client(persist_directory)
    collection = client.get_collection(name=COLLECTION_NAME)

    # Convert the user question into an embedding vector
    query_vector = embed([query])[0]

    # Query ChromaDB for nearest vectors
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    hits: list[dict[str, Any]] = []
    if not results or not results["ids"] or not results["ids"][0]:
        return hits

    ids = results["ids"][0]
    docs = results["documents"][0] if results.get("documents") else []
    metadatas = results["metadatas"][0] if results.get("metadatas") else []
    distances = results["distances"][0] if results.get("distances") else []

    for i in range(len(ids)):
        chunk_id = ids[i]
        text = docs[i] if i < len(docs) else ""
        meta = metadatas[i] if i < len(metadatas) else {}
        distance = distances[i] if i < len(distances) else 1.0

        # Convert cosine distance to a similarity score between 0.0 and 1.0
        similarity = round(max(0.0, 1.0 - distance), 4)

        hits.append({
            "id": chunk_id,
            "text": text,
            "score": similarity,
            "similarity": similarity,
            "filename": meta.get("filename", chunk_id.split("#")[0]),
            "heading": meta.get("heading", ""),
        })

    return hits
