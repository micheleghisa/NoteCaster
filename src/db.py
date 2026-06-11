import os
import uuid
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


def create_notebook(name: str, user_id: str, notebook_id: str = None) -> dict:
    if not name or not name.strip():
        raise ValueError("Notebook name cannot be empty.")
    if notebook_id is None:
        notebook_id = uuid.uuid4().hex[:12]
    created_at = datetime.datetime.now().isoformat()
    client = _get_client()
    existing = client.table("notebooks").select("id").eq("name", name.strip()).eq("user_id", user_id).execute()
    if existing.data:
        raise ValueError(f"Notebook name '{name}' already exists.")
    result = client.table("notebooks").insert({
        "id": notebook_id,
        "name": name.strip(),
        "created_at": created_at,
        "user_id": user_id,
    }).execute()
    return result.data[0]


def get_notebooks(user_id: str) -> list:
    result = _get_client().table("notebooks").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    return result.data


def get_notebook(notebook_id: str, user_id: str) -> dict | None:
    result = _get_client().table("notebooks").select("*").eq("id", notebook_id).eq("user_id", user_id).execute()
    return result.data[0] if result.data else None


def get_notebook_by_name(name: str, user_id: str) -> dict | None:
    result = _get_client().table("notebooks").select("*").eq("name", name).eq("user_id", user_id).execute()
    return result.data[0] if result.data else None


def list_notebooks(user_id: str) -> list:
    result = _get_client().table("notebooks").select("*").eq("user_id", user_id).order("created_at", desc=False).execute()
    return result.data


def delete_notebook(notebook_id: str, user_id: str) -> None:
    _get_client().table("notebooks").delete().eq("id", notebook_id).eq("user_id", user_id).execute()


def rename_notebook(notebook_id: str, new_name: str, user_id: str) -> None:
    _get_client().table("notebooks").update({"name": new_name}).eq("id", notebook_id).eq("user_id", user_id).execute()


def notebook_exists(notebook_id: str, user_id: str) -> bool:
    result = _get_client().table("notebooks").select("id").eq("id", notebook_id).eq("user_id", user_id).execute()
    return bool(result.data)
