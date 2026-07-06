from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import json
import sqlite3
from typing import Any, Iterator


class LocalSessionStore:
    def __init__(self, db_path: str | Path, max_sessions: int = 20) -> None:
        self.db_path = Path(db_path)
        self.max_sessions = max(1, int(max_sessions))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _init_db(self) -> None:
        with self._connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS phase6_sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    image_path TEXT,
                    detection_json TEXT,
                    treatment_json TEXT,
                    sync_status TEXT NOT NULL DEFAULT 'pending',
                    backend_json TEXT,
                    inventory_json TEXT,
                    telegram_json TEXT,
                    error_json TEXT
                )
                """
            )

    def create_session(self, session_id: str, image_path: str | Path | None = None) -> None:
        with self._connection() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO phase6_sessions (
                    session_id,
                    image_path,
                    sync_status,
                    updated_at
                )
                VALUES (?, ?, 'captured', CURRENT_TIMESTAMP)
                """,
                (session_id, str(image_path) if image_path is not None else None),
            )
        self.prune_old_sessions()

    def update_session(self, session_id: str, **fields: Any) -> None:
        if not fields:
            return
        allowed = {
            "image_path",
            "detection_json",
            "treatment_json",
            "sync_status",
            "backend_json",
            "inventory_json",
            "telegram_json",
            "error_json",
        }
        unknown = set(fields) - allowed
        if unknown:
            raise ValueError(f"Unknown phase6 session fields: {sorted(unknown)}")

        assignments = ["updated_at = CURRENT_TIMESTAMP"]
        values: list[Any] = []
        for key, value in fields.items():
            assignments.append(f"{key} = ?")
            if key.endswith("_json") and value is not None:
                values.append(_json(value))
            elif key == "image_path" and value is not None:
                values.append(str(value))
            else:
                values.append(value)
        values.append(session_id)

        with self._connection() as connection:
            connection.execute(
                f"UPDATE phase6_sessions SET {', '.join(assignments)} WHERE session_id = ?",
                values,
            )
        self.prune_old_sessions()

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM phase6_sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        return _decode_row(dict(row))

    def list_sessions(self) -> list[dict[str, Any]]:
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM phase6_sessions
                ORDER BY created_at DESC, session_id DESC
                """
            ).fetchall()
        return [_decode_row(dict(row)) for row in rows]

    def prune_old_sessions(self) -> None:
        with self._connection() as connection:
            connection.execute(
                """
                DELETE FROM phase6_sessions
                WHERE session_id NOT IN (
                    SELECT session_id
                    FROM phase6_sessions
                    ORDER BY created_at DESC, session_id DESC
                    LIMIT ?
                )
                """,
                (self.max_sessions,),
            )


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, default=str)


def _decode_row(row: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "detection_json",
        "treatment_json",
        "backend_json",
        "inventory_json",
        "telegram_json",
        "error_json",
    ):
        if row.get(key):
            row[key] = json.loads(row[key])
    return row
