from __future__ import annotations

from collections.abc import Callable
import logging
import time
from typing import TypeVar


T = TypeVar("T")
logger = logging.getLogger(__name__)


class RetryPolicy:
    def __init__(self, attempts: int = 3, backoff_seconds: float = 1.0) -> None:
        self.attempts = max(1, attempts)
        self.backoff_seconds = max(0.0, backoff_seconds)

    def run(self, label: str, func: Callable[[], T]) -> T:
        last_error: Exception | None = None
        for attempt in range(1, self.attempts + 1):
            try:
                return func()
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Retryable call failed",
                    extra={
                        "_operation": label,
                        "_attempt": attempt,
                        "_max_attempts": self.attempts,
                        "_error": str(exc),
                    },
                )
                if attempt < self.attempts and self.backoff_seconds:
                    time.sleep(self.backoff_seconds * attempt)
        assert last_error is not None
        raise last_error

