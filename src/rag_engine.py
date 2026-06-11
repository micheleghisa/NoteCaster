import os
import chromadb
from chromadb.utils import embedding_functions

CHROMA_PATH = os.path.join(os.path.dirname(__file__), '..', 'chroma_db')


def _get_collection(notebook_id: str):
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    ef = embedding_functions.DefaultEmbeddingFunction()
    return client.get_or_create_collection(name=notebook_id, embedding_function=ef)


def index_document(notebook_id: str, doc_name: str, chunks: list[str]) -> int:
    """Index document chunks into the collection.

    IDs are formatted as "{i}_{doc_name}" (index first to avoid parsing issues
    with special chars in doc names). Skips chunks already indexed.
    Returns count of NEW chunks added.
    """
    collection = _get_collection(notebook_id)
    ids = [f"{i}_{doc_name}" for i in range(len(chunks))]
    existing = set(collection.get()["ids"])
    new_ids = [id_ for id_ in ids if id_ not in existing]
    new_chunks = [chunks[i] for i, id_ in enumerate(ids) if id_ not in existing]
    metadatas = [{"doc_name": doc_name} for _ in new_chunks]
    if new_chunks:
        collection.add(documents=new_chunks, ids=new_ids, metadatas=metadatas)
    return len(new_chunks)


def query_context(notebook_id: str, question: str, n_results: int = 6) -> str:
    """Query the collection and return relevant chunks joined by separators.

    Returns "" if collection is empty or not found.
    Caps n_results at collection.count().
    """
    try:
        collection = _get_collection(notebook_id)
        count = collection.count()
        if count == 0:
            return ""
        capped = min(n_results, count)
        results = collection.query(query_texts=[question], n_results=capped)
        return "\n\n---\n\n".join(results["documents"][0])
    except Exception:
        return ""


def get_indexed_docs(notebook_id: str) -> list[str]:
    """Return sorted unique list of doc_names indexed in the collection.

    Tries metadata first; falls back to parsing chunk IDs (split on first "_",
    take the rest) if metadata is unavailable.
    """
    try:
        collection = _get_collection(notebook_id)
        if collection.count() == 0:
            return []
        data = collection.get()
        doc_names: set[str] = set()

        metadatas = data.get("metadatas") or []
        if metadatas and any(m and "doc_name" in m for m in metadatas):
            for m in metadatas:
                if m and "doc_name" in m:
                    doc_names.add(m["doc_name"])
        else:
            # Fallback: handle both old format "doc_name_i" and new format "i_doc_name"
            for id_ in data.get("ids", []):
                right = id_.rsplit("_", 1)
                left = id_.split("_", 1)
                if len(right) == 2 and right[1].isdigit():
                    # Old format: doc_name_i → doc_name is left part
                    if right[0]:
                        doc_names.add(right[0])
                elif len(left) == 2 and left[0].isdigit():
                    # New format: i_doc_name → doc_name is right part
                    if left[1]:
                        doc_names.add(left[1])

        return sorted(doc_names)
    except Exception:
        return []


def get_full_text(notebook_id: str, max_chars: int = 15000) -> str:
    """Retrieve ALL chunks from the collection (no query), joined with newlines.

    Truncates to max_chars. Returns "" if nothing found.
    """
    try:
        collection = _get_collection(notebook_id)
        if collection.count() == 0:
            return ""
        data = collection.get()
        documents = data.get("documents") or []
        full_text = "\n\n".join(doc for doc in documents if doc)
        return full_text[:max_chars]
    except Exception:
        return ""


def get_doc_text(notebook_id: str, doc_name: str, max_chars: int = 15000) -> str:
    """Retrieve all chunks from a specific document, filtered by doc_name."""
    try:
        collection = _get_collection(notebook_id)
        if collection.count() == 0:
            return ""
        data = collection.get()
        documents = data.get("documents") or []
        metadatas = data.get("metadatas") or []
        doc_chunks = [
            doc for doc, meta in zip(documents, metadatas)
            if meta and meta.get("doc_name") == doc_name and doc
        ]
        return "\n\n".join(doc_chunks)[:max_chars]
    except Exception:
        return ""


def delete_notebook_index(notebook_id: str) -> None:
    """Delete the collection for a notebook. Ignores errors if not found."""
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        client.delete_collection(notebook_id)
    except Exception:
        pass
