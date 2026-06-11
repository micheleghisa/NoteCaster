import os
import datetime

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
    content = '\n\n'.join(chunks)
    client = _get_client()
    client.table("documents").upsert({
        "notebook_id": notebook_id,
        "doc_name": doc_name,
        "content": content,
        "created_at": datetime.datetime.now().isoformat(),
    }, on_conflict="notebook_id,doc_name").execute()
    return len(chunks)


def get_indexed_docs(notebook_id: str) -> list:
    result = _get_client().table("documents").select("doc_name").eq("notebook_id", notebook_id).order("doc_name").execute()
    return [row["doc_name"] for row in result.data]


def get_doc_text(notebook_id: str, doc_name: str) -> str:
    result = _get_client().table("documents").select("content").eq("notebook_id", notebook_id).eq("doc_name", doc_name).execute()
    return result.data[0]["content"] if result.data else ""


def get_full_text(notebook_id: str) -> str:
    result = _get_client().table("documents").select("content").eq("notebook_id", notebook_id).order("doc_name").execute()
    return '\n\n'.join(row["content"] for row in result.data)


def query_context(notebook_id: str, question: str, n_results: int = 6) -> str:
    """Keyword-based context retrieval — scores stored chunks by word overlap with the question."""
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
        'the', 'a', 'an', 'of', 'to', 'in', 'for', 'is', 'it', 'be', 'as',
        'at', 'so', 'we', 'he', 'by', 'or', 'do', 'and', 'are', 'with', 'this',
    }
    question_words = {w for w in question.lower().split() if w not in _STOP and len(w) > 2}

    scored = []
    for chunk in chunks:
        chunk_words = set(chunk.lower().split())
        score = len(question_words & chunk_words)
        scored.append((score, chunk))

    scored.sort(reverse=True)
    top = [c for _, c in scored[:n_results]]
    return '\n\n---\n\n'.join(top)


def delete_notebook_index(notebook_id: str) -> None:
    _get_client().table("documents").delete().eq("notebook_id", notebook_id).execute()
