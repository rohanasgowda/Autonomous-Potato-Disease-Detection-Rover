from __future__ import annotations

import argparse
import json
from pathlib import Path

from phase3.app.clients.openrouter import OpenRouterClient
from phase3.app.config.settings import Settings
from phase3.app.integrations.backend import BackendClient
from phase3.app.notifications.telegram import TelegramClient
from phase3.app.services.pipeline import TreatmentPipeline
from phase3.app.storage.audit_store import AuditStore
from phase3.app.utils.logging import configure_logging
from phase3.app.utils.retry import RetryPolicy


def build_pipeline(settings: Settings) -> TreatmentPipeline:
    retry_policy = RetryPolicy(
        attempts=settings.retry_attempts,
        backoff_seconds=settings.retry_backoff_seconds,
    )
    return TreatmentPipeline(
        openrouter_client=OpenRouterClient(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            model=settings.openrouter_model,
            temperature=settings.openrouter_temperature,
            max_tokens=settings.openrouter_max_tokens,
            timeout_seconds=settings.request_timeout_seconds,
            retry_policy=retry_policy,
        ),
        backend_client=BackendClient(
            base_url=settings.backend_base_url,
            username=settings.backend_username,
            password=settings.backend_password,
            timeout_seconds=settings.request_timeout_seconds,
            retry_policy=retry_policy,
        ),
        telegram_client=TelegramClient(
            bot_token=settings.telegram_bot_token,
            chat_id=settings.telegram_chat_id,
            base_url=settings.telegram_base_url,
            timeout_seconds=settings.request_timeout_seconds,
            retry_policy=retry_policy,
        ),
        audit_store=AuditStore(settings.audit_db_path),
        model_name=settings.openrouter_model,
        backend_vendor_id=settings.backend_vendor_id,
    )


def resolve_env_file(env_file: str) -> str:
    requested = Path(env_file)
    if requested.exists():
        return str(requested)
    phase3_env = Path("phase3") / env_file
    if phase3_env.exists():
        return str(phase3_env)
    return env_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Phase 3 treatment agent pipeline.")
    parser.add_argument("--input", required=True, help="Path to detection JSON from Raspberry Pi inference.")
    parser.add_argument("--farm-size-acres", required=True, type=float)
    parser.add_argument("--number-of-plants", required=True, type=int)
    parser.add_argument("--country", default="India")
    parser.add_argument("--language", default="English")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--skip-backend", action="store_true")
    parser.add_argument("--skip-telegram", action="store_true")
    args = parser.parse_args()

    settings = Settings.from_env(resolve_env_file(args.env_file))
    configure_logging(settings.log_level)
    pipeline = build_pipeline(settings)
    detection_payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = pipeline.run(
        detection_payload=detection_payload,
        farm_size_acres=args.farm_size_acres,
        number_of_plants=args.number_of_plants,
        country=args.country,
        language=args.language,
        sync_backend=not args.skip_backend,
        send_telegram=not args.skip_telegram,
    )
    print(json.dumps(result.model_dump(mode="json"), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
