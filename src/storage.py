import os
import datetime
import math

from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

_client: Client | None = None


def _get_client() -> Client:
    global _client
    if _client is None:
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
        _client = create_client(url, key)
    return _client


def index_document(notebook_id: str, doc_name: str, chunks: list) -> int:
    from src.embeddings import embed_texts

    client = _get_client()

    # Keep the full-text blob for podcast/notes generation.
    # Delete-then-insert avoids needing a DB-level unique constraint.
    content = '\n\n'.join(chunks)
    client.table("documents").delete() \
        .eq("notebook_id", notebook_id) \
        .eq("doc_name", doc_name) \
        .execute()
    client.table("documents").insert({
        "notebook_id": notebook_id,
        "doc_name": doc_name,
        "content": content,
        "created_at": datetime.datetime.now().isoformat(),
    }).execute()

    # Store each chunk individually for retrieval
    try:
        client.table("document_chunks").delete() \
            .eq("notebook_id", notebook_id) \
            .eq("doc_name", doc_name) \
            .execute()

        embeddings = embed_texts(chunks)  # None if no OPENAI_API_KEY

        rows = []
        for i, chunk in enumerate(chunks):
            row = {
                "notebook_id": notebook_id,
                "doc_name": doc_name,
                "chunk_index": i,
                "content": chunk,
            }
            if embeddings is not None:
                row["embedding"] = embeddings[i]
            rows.append(row)

        for i in range(0, len(rows), 50):
            client.table("document_chunks").insert(rows[i:i + 50]).execute()
    except Exception:
        pass  # document_chunks table may not exist yet; full-text fallback still works

    return len(chunks)


def get_indexed_docs(notebook_id: str) -> list:
    result = _get_client().table("documents").select("doc_name") \
        .eq("notebook_id", notebook_id).order("doc_name").execute()
    return [row["doc_name"] for row in result.data]


def get_doc_text(notebook_id: str, doc_name: str) -> str:
    result = _get_client().table("documents").select("content") \
        .eq("notebook_id", notebook_id).eq("doc_name", doc_name).execute()
    return result.data[0]["content"] if result.data else ""


def get_full_text(notebook_id: str) -> str:
    result = _get_client().table("documents").select("content") \
        .eq("notebook_id", notebook_id).order("doc_name").execute()
    return '\n\n'.join(row["content"] for row in result.data)


def query_context(notebook_id: str, question: str, n_results: int = 6) -> str:
    from src.embeddings import embed_query

    # ── 1. Semantic search via pgvector ───────────────────────────────────────
    q_embedding = embed_query(question)
    if q_embedding is not None:
        try:
            result = _get_client().rpc("match_chunks", {
                "query_embedding": q_embedding,
                "match_notebook_id": notebook_id,
                "match_count": n_results,
            }).execute()
            if result.data:
                return '\n\n---\n\n'.join(row["content"] for row in result.data)
        except Exception:
            pass

    # ── 2. BM25 fallback over stored chunks ───────────────────────────────────
    return _bm25_search(notebook_id, question, n_results)


def _bm25_search(notebook_id: str, question: str, n_results: int) -> str:
    """BM25-style keyword search. Uses document_chunks if available, else documents."""
    chunks = []
    try:
        result = _get_client().table("document_chunks").select("content") \
            .eq("notebook_id", notebook_id).execute()
        chunks = [row["content"] for row in result.data] if result.data else []
    except Exception:
        pass

    if not chunks:
        full_text = get_full_text(notebook_id)
        if not full_text:
            return ""
        chunks = [c.strip() for c in full_text.split('\n\n') if len(c.strip()) > 80]
        if not chunks:
            return full_text[:4000]

    _STOP = {
        'il', 'la', 'lo', 'le', 'i', 'gli', 'un', 'una', 'di', 'a', 'da', 'in',
        'con', 'su', 'per', 'tra', 'fra', 'che', 'e', 'è', 'non', 'si', 'del',
        'della', 'dei', 'degli', 'al', 'alla', 'ai', 'agli', 'nel', 'nella',
        'the', 'an', 'of', 'to', 'for', 'is', 'it', 'be', 'as',
        'at', 'so', 'we', 'he', 'by', 'or', 'do', 'and', 'are', 'with', 'this',
    }

    q_words = [w.lower() for w in question.split() if w.lower() not in _STOP and len(w) > 2]
    if not q_words:
        return '\n\n---\n\n'.join(chunks[:n_results])

    N = len(chunks)
    avg_len = sum(len(c.split()) for c in chunks) / N

    # IDF for each unique query word
    idf: dict[str, float] = {}
    for w in set(q_words):
        df = sum(1 for c in chunks if w in c.lower())
        idf[w] = math.log((N - df + 0.5) / (df + 0.5) + 1)

    k1, b = 1.5, 0.75
    scored = []
    for chunk in chunks:
        words = chunk.lower().split()
        dl = len(words)
        score = 0.0
        for w in q_words:
            tf = words.count(w)
            if tf:
                score += idf[w] * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / avg_len))
        scored.append((score, chunk))

    scored.sort(reverse=True)
    top = [c for _, c in scored[:n_results]]
    return '\n\n---\n\n'.join(top)


def delete_notebook_index(notebook_id: str) -> None:
    client = _get_client()
    client.table("documents").delete().eq("notebook_id", notebook_id).execute()
    try:
        client.table("document_chunks").delete().eq("notebook_id", notebook_id).execute()
    except Exception:
        pass
