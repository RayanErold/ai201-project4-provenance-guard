"""Structured audit logger backed by SQLite.

Every classification, appeal and status change is recorded as a JSON-serialisable
event so the system can reconstruct the full provenance history of any content_id.
"""
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AuditStore:
    """Thin wrapper around SQLite for audit logs and content status."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS audit_log (
                    id          TEXT PRIMARY KEY,
                    content_id  TEXT NOT NULL,
                    event_type  TEXT NOT NULL,
                    payload     TEXT NOT NULL,
                    created_at  TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS content_status (
                    content_id  TEXT PRIMARY KEY,
                    creator_id  TEXT,
                    attribution TEXT,
                    confidence  REAL,
                    label       TEXT,
                    status      TEXT NOT NULL,
                    created_at  TEXT NOT NULL,
                    updated_at  TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS certificates (
                    creator_id  TEXT PRIMARY KEY,
                    verified    INTEGER NOT NULL DEFAULT 0,
                    issued_at   TEXT
                );
                """
            )

    # ------------------------------------------------------------------ events
    def log_event(self, content_id: str, event_type: str, payload: dict[str, Any]) -> str:
        event_id = str(uuid.uuid4())
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO audit_log (id, content_id, event_type, payload, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (event_id, content_id, event_type, json.dumps(payload), _utc_now()),
            )
        return event_id

    def recent_events(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM audit_log ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [
            {
                "id": r["id"],
                "content_id": r["content_id"],
                "event_type": r["event_type"],
                "payload": json.loads(r["payload"]),
                "created_at": r["created_at"],
            }
            for r in rows
        ]

    # ------------------------------------------------------------------ status
    def upsert_content(
        self,
        content_id: str,
        creator_id: str,
        attribution: str,
        confidence: float,
        label: str,
        status: str = "classified",
    ) -> None:
        now = _utc_now()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO content_status
                    (content_id, creator_id, attribution, confidence, label, status,
                     created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(content_id) DO UPDATE SET
                    attribution=excluded.attribution,
                    confidence=excluded.confidence,
                    label=excluded.label,
                    status=excluded.status,
                    updated_at=excluded.updated_at
                """,
                (content_id, creator_id, attribution, confidence, label, status, now, now),
            )

    def get_content(self, content_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM content_status WHERE content_id = ?", (content_id,)
            ).fetchone()
        return dict(row) if row else None

    def update_status(self, content_id: str, status: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute(
                "UPDATE content_status SET status = ?, updated_at = ? WHERE content_id = ?",
                (status, _utc_now(), content_id),
            )
            return cur.rowcount > 0

    def all_content(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM content_status").fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------ certificates
    def set_certificate(self, creator_id: str, verified: bool = True) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO certificates (creator_id, verified, issued_at) VALUES (?, ?, ?) "
                "ON CONFLICT(creator_id) DO UPDATE SET verified=excluded.verified, "
                "issued_at=excluded.issued_at",
                (creator_id, 1 if verified else 0, _utc_now()),
            )

    def is_verified_human(self, creator_id: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT verified FROM certificates WHERE creator_id = ?", (creator_id,)
            ).fetchone()
        return bool(row and row["verified"])
