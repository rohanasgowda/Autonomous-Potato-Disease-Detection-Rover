from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


def _float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return float(value)


@dataclass(frozen=True)
class Settings:
    openrouter_api_key: str | None
    openrouter_base_url: str
    openrouter_model: str
    openrouter_temperature: float
    openrouter_max_tokens: int
    request_timeout_seconds: float
    retry_attempts: int
    retry_backoff_seconds: float

    backend_base_url: str | None
    backend_username: str | None
    backend_password: str | None
    backend_vendor_id: str

    telegram_bot_token: str | None
    telegram_chat_id: str | None
    telegram_base_url: str

    audit_db_path: Path
    log_level: str

    @classmethod
    def from_env(cls, env_file: str | Path | None = None) -> "Settings":
        if env_file is not None:
            load_env_file(Path(env_file))

        return cls(
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
            openrouter_base_url=os.getenv(
                "OPENROUTER_BASE_URL",
                "https://openrouter.ai/api/v1",
            ).rstrip("/"),
            openrouter_model=os.getenv(
                "OPENROUTER_MODEL",
                "google/gemini-3.1-flash-lite",
            ),
            openrouter_temperature=_float_env("OPENROUTER_TEMPERATURE", 0.2),
            openrouter_max_tokens=_int_env("OPENROUTER_MAX_TOKENS", 1800),
            request_timeout_seconds=_float_env("REQUEST_TIMEOUT_SECONDS", 30.0),
            retry_attempts=_int_env("RETRY_ATTEMPTS", 3),
            retry_backoff_seconds=_float_env("RETRY_BACKOFF_SECONDS", 1.0),
            backend_base_url=(os.getenv("BACKEND_BASE_URL") or "").rstrip("/") or None,
            backend_username=os.getenv("BACKEND_USERNAME"),
            backend_password=os.getenv("BACKEND_PASSWORD"),
            backend_vendor_id=os.getenv("BACKEND_VENDOR_ID", "vendor_001"),
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
            telegram_base_url=os.getenv(
                "TELEGRAM_BASE_URL",
                "https://api.telegram.org",
            ).rstrip("/"),
            audit_db_path=Path(os.getenv("AUDIT_DB_PATH", "logs/phase3_audit.db")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )
