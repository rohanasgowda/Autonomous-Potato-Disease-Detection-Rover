from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Any


class AuditStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS treatment_audit (
                    run_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    model_name TEXT,
                    validation_status TEXT NOT NULL,
                    detection_json TEXT,
                    agent_input_json TEXT,
                    openrouter_request_json TEXT,
                    raw_response_json TEXT,
                    parsed_response_json TEXT,
                    backend_result_json TEXT,
                    inventory_result_json TEXT,
                    telegram_result_json TEXT,
                    error_message TEXT
                )
                """
            )

    def create_run(
        self,
        run_id: str,
        model_name: str,
        detection_json: dict[str, Any],
        agent_input_json: dict[str, Any],
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO treatment_audit (
                    run_id,
                    model_name,
                    validation_status,
                    detection_json,
                    agent_input_json
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    model_name,
                    "started",
                    _json(detection_json),
                    _json(agent_input_json),
                ),
            )

    def update_run(self, run_id: str, **fields: Any) -> None:
        if not fields:
            return
        allowed = {
            "validation_status",
            "openrouter_request_json",
            "raw_response_json",
            "parsed_response_json",
            "backend_result_json",
            "inventory_result_json",
            "telegram_result_json",
            "error_message",
        }
        unknown = set(fields) - allowed
        if unknown:
            raise ValueError(f"Unknown audit fields: {sorted(unknown)}")
        assignments = ["updated_at = CURRENT_TIMESTAMP"]
        values: list[Any] = []
        for key, value in fields.items():
            assignments.append(f"{key} = ?")
            if key.endswith("_json") and value is not None:
                values.append(_json(value))
            else:
                values.append(value)
        values.append(run_id)
        with self._connect() as connection:
            connection.execute(
                f"UPDATE treatment_audit SET {', '.join(assignments)} WHERE run_id = ?",
                values,
            )

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM treatment_audit WHERE run_id = ?",
                (run_id,),
            ).fetchone()
        if row is None:
            return None
        return dict(row)


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, default=str)

