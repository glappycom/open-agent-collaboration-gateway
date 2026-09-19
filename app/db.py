import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from .config import settings


def _conn():
    path = Path(settings.database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                provider TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id, id)"
        )


def log_message(conversation_id: str, provider: str, role: str, content: str, metadata: dict | None = None):
    with _conn() as conn:
        conn.execute(
            "INSERT INTO messages(conversation_id, provider, role, content, metadata, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                conversation_id,
                provider,
                role,
                content,
                json.dumps(metadata or {}),
                datetime.now(timezone.utc).isoformat(),
            ),
        )


def load_messages(conversation_id: str, limit: int = 50):
    with _conn() as conn:
        rows = conn.execute(
            "SELECT provider, role, content, metadata, created_at FROM messages WHERE conversation_id = ? ORDER BY id DESC LIMIT ?",
            (conversation_id, limit),
        ).fetchall()
    return [dict(r) for r in reversed(rows)]
