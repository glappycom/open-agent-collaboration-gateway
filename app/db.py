import json
import sqlite3
from datetime import datetime, timezone, timedelta
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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS idempotency_records (
                idempotency_key TEXT PRIMARY KEY,
                request_hash TEXT NOT NULL,
                response_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS telemetry_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trace_id TEXT NOT NULL,
                conversation_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                provider TEXT,
                model TEXT,
                latency_ms INTEGER,
                input_tokens INTEGER,
                output_tokens INTEGER,
                total_tokens INTEGER,
                retry_count INTEGER NOT NULL DEFAULT 0,
                estimated_cost_usd REAL,
                metadata TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_telemetry_trace ON telemetry_events(trace_id, id)"
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


def get_idempotency_record(idempotency_key: str, ttl_seconds: int) -> dict | None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT idempotency_key, request_hash, response_json, created_at FROM idempotency_records WHERE idempotency_key = ?",
            (idempotency_key,),
        ).fetchone()

        if row is None:
            return None

        created_at = datetime.fromisoformat(row["created_at"])
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        if ttl_seconds > 0 and datetime.now(timezone.utc) - created_at > timedelta(seconds=ttl_seconds):
            conn.execute(
                "DELETE FROM idempotency_records WHERE idempotency_key = ?",
                (idempotency_key,),
            )
            return None

        return dict(row)


def store_idempotency_record(idempotency_key: str, request_hash: str, response_json: str) -> None:
    with _conn() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO idempotency_records(idempotency_key, request_hash, response_json, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                idempotency_key,
                request_hash,
                response_json,
                datetime.now(timezone.utc).isoformat(),
            ),
        )



def log_telemetry(
    *,
    trace_id: str,
    conversation_id: str,
    event_type: str,
    provider: str | None = None,
    model: str | None = None,
    latency_ms: int | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    total_tokens: int | None = None,
    retry_count: int = 0,
    estimated_cost_usd: float | None = None,
    metadata: dict | None = None,
) -> None:
    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO telemetry_events(
                trace_id, conversation_id, event_type, provider, model, latency_ms,
                input_tokens, output_tokens, total_tokens, retry_count,
                estimated_cost_usd, metadata, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trace_id,
                conversation_id,
                event_type,
                provider,
                model,
                latency_ms,
                input_tokens,
                output_tokens,
                total_tokens,
                retry_count,
                estimated_cost_usd,
                json.dumps(metadata or {}),
                datetime.now(timezone.utc).isoformat(),
            ),
        )


def load_trace_telemetry(trace_id: str, limit: int = 200) -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            """
            SELECT trace_id, conversation_id, event_type, provider, model, latency_ms,
                   input_tokens, output_tokens, total_tokens, retry_count,
                   estimated_cost_usd, metadata, created_at
            FROM telemetry_events
            WHERE trace_id = ?
            ORDER BY id ASC
            LIMIT ?
            """,
            (trace_id, limit),
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["metadata"] = json.loads(item["metadata"] or "{}")
        result.append(item)
    return result


def telemetry_summary() -> dict:
    with _conn() as conn:
        row = conn.execute(
            """
            SELECT
                COUNT(*) AS event_count,
                SUM(CASE WHEN event_type = 'provider_response' THEN 1 ELSE 0 END) AS provider_calls,
                SUM(COALESCE(input_tokens, 0)) AS input_tokens,
                SUM(COALESCE(output_tokens, 0)) AS output_tokens,
                SUM(COALESCE(total_tokens, 0)) AS total_tokens,
                SUM(COALESCE(retry_count, 0)) AS retries,
                SUM(COALESCE(estimated_cost_usd, 0.0)) AS estimated_cost_usd,
                AVG(CASE WHEN latency_ms IS NOT NULL THEN latency_ms END) AS avg_latency_ms
            FROM telemetry_events
            """
        ).fetchone()
    return dict(row) if row else {}
