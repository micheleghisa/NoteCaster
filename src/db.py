import sqlite3
import os
import uuid
import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'notebooklm.db')


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS notebooks (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL UNIQUE,
            created_at  TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def create_notebook(name: str, notebook_id: str = None) -> dict:
    if not name or not name.strip():
        raise ValueError("Notebook name cannot be empty.")
    if notebook_id is None:
        notebook_id = uuid.uuid4().hex[:12]
    created_at = datetime.datetime.now().isoformat()
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO notebooks (id, name, created_at) VALUES (?, ?, ?)",
            (notebook_id, name, created_at)
        )
        conn.commit()
        row = conn.execute(
            "SELECT id, name, created_at FROM notebooks WHERE id = ?",
            (notebook_id,)
        ).fetchone()
        if row is None:
            raise ValueError(f"Notebook name '{name}' already exists.")
        return dict(row)
    finally:
        conn.close()


def get_notebooks() -> list:
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT id, name, created_at FROM notebooks ORDER BY created_at DESC"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_notebook(notebook_id: str) -> dict | None:
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT id, name, created_at FROM notebooks WHERE id = ?",
            (notebook_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_notebook_by_name(name: str) -> dict | None:
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT id, name, created_at FROM notebooks WHERE name = ?",
            (name,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def list_notebooks() -> list:
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT id, name, created_at FROM notebooks ORDER BY created_at ASC"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def delete_notebook(notebook_id: str) -> None:
    conn = _get_conn()
    try:
        conn.execute("DELETE FROM notebooks WHERE id = ?", (notebook_id,))
        conn.commit()
    finally:
        conn.close()


def rename_notebook(notebook_id: str, new_name: str) -> None:
    conn = _get_conn()
    try:
        conn.execute(
            "UPDATE notebooks SET name = ? WHERE id = ?",
            (new_name, notebook_id)
        )
        conn.commit()
    finally:
        conn.close()


def notebook_exists(notebook_id: str) -> bool:
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT 1 FROM notebooks WHERE id = ?",
            (notebook_id,)
        ).fetchone()
        return row is not None
    finally:
        conn.close()


init_db()
