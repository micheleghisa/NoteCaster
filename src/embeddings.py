import os
import requests

_VOYAGE_URL = "https://api.voyageai.com/v1/embeddings"
_VOYAGE_MODEL = "voyage-4-large"


def _call_api(texts: list[str], input_type: str) -> list[list[float]] | None:
    key = os.environ.get("VOYAGE_API_KEY")
    if not key:
        return None
    try:
        embeddings = []
        for i in range(0, len(texts), 128):
            batch = texts[i:i + 128]
            resp = requests.post(
                _VOYAGE_URL,
                headers={"Authorization": f"Bearer {key}"},
                json={"model": _VOYAGE_MODEL, "input": batch, "input_type": input_type},
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()["data"]
            # data is sorted by index, but sort explicitly to be safe
            data.sort(key=lambda x: x["index"])
            embeddings.extend(item["embedding"] for item in data)
        return embeddings
    except Exception:
        return None


def embed_texts(texts: list[str]) -> list[list[float]] | None:
    return _call_api(texts, "document")


def embed_query(text: str) -> list[float] | None:
    result = _call_api([text], "query")
    return result[0] if result else None
