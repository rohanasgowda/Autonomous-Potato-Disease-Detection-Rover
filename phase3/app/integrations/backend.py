from __future__ import annotations

import logging
from typing import Any

import httpx

from phase3.app.schemas.detection import DetectionCreate
from phase3.app.schemas.inventory import InventoryCheckRequest, InventoryCheckResponse
from phase3.app.schemas.treatment import TreatmentAgentInput, TreatmentAgentOutput
from phase3.app.utils.errors import ConfigurationError
from phase3.app.utils.retry import RetryPolicy


logger = logging.getLogger(__name__)


class BackendClient:
    def __init__(
        self,
        base_url: str | None,
        username: str | None,
        password: str | None,
        timeout_seconds: float,
        retry_policy: RetryPolicy,
    ) -> None:
        self.base_url = base_url.rstrip("/") if base_url else None
        self.username = username
        self.password = password
        self.timeout_seconds = timeout_seconds
        self.retry_policy = retry_policy
        self._token: str | None = None

    @property
    def is_configured(self) -> bool:
        return bool(self.base_url and self.username and self.password)

    def _require_config(self) -> None:
        if not self.is_configured:
            raise ConfigurationError(
                "BACKEND_BASE_URL, BACKEND_USERNAME, and BACKEND_PASSWORD are required for backend sync."
            )

    def _headers(self) -> dict[str, str]:
        if not self._token:
            self.login()
        return {"Authorization": f"Bearer {self._token}"}

    def login(self) -> None:
        self._require_config()

        def send() -> str:
            assert self.base_url is not None
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(
                    f"{self.base_url}/auth/login",
                    json={"username": self.username, "password": self.password},
                )
                response.raise_for_status()
                payload = response.json()
                return payload["access_token"]

        self._token = self.retry_policy.run("backend.auth.login", send)
        logger.info("Backend login succeeded", extra={"_backend_base_url": self.base_url})

    def upload_detection(self, detection: DetectionCreate) -> dict[str, Any]:
        self._require_config()

        def send() -> dict[str, Any]:
            assert self.base_url is not None
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(
                    f"{self.base_url}/detections",
                    headers=self._headers(),
                    json=detection.model_dump(mode="json"),
                )
                if response.status_code == 409:
                    existing = self.find_detection_by_session_id(detection.session_id)
                    if existing is not None:
                        return existing
                response.raise_for_status()
                return response.json()

        return self.retry_policy.run("backend.detections.create", send)

    def find_detection_by_session_id(self, session_id: str) -> dict[str, Any] | None:
        assert self.base_url is not None
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.get(
                f"{self.base_url}/detections",
                headers={"Authorization": f"Bearer {self._token}"},
                params={"limit": 100, "offset": 0},
            )
            response.raise_for_status()
            for item in response.json():
                if item.get("session_id") == session_id:
                    return item
        return None

    def upload_recommendation(
        self,
        detection_id: int,
        model_name: str,
        raw_request: TreatmentAgentInput,
        raw_response: TreatmentAgentOutput,
    ) -> dict[str, Any]:
        self._require_config()
        payload = {
            "detection_session_id": detection_id,
            "model_provider": "openrouter",
            "model_name": model_name,
            "raw_request_json": raw_request.model_dump(mode="json"),
            "raw_response_json": raw_response.model_dump(mode="json"),
        }

        def send() -> dict[str, Any]:
            assert self.base_url is not None
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(
                    f"{self.base_url}/recommendations",
                    headers=self._headers(),
                    json=payload,
                )
                response.raise_for_status()
                return response.json()

        return self.retry_policy.run("backend.recommendations.create", send)

    def check_inventory(self, request: InventoryCheckRequest) -> InventoryCheckResponse:
        self._require_config()

        def send() -> InventoryCheckResponse:
            assert self.base_url is not None
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(
                    f"{self.base_url}/inventory/check",
                    headers=self._headers(),
                    json=request.model_dump(mode="json"),
                )
                response.raise_for_status()
                return InventoryCheckResponse.model_validate(response.json())

        return self.retry_policy.run("backend.inventory.check", send)

    def trigger_backend_telegram(
        self,
        detection_id: int,
        recommendation_id: int | None,
        farmer_chat_id: str | None,
    ) -> dict[str, Any]:
        self._require_config()
        payload = {
            "detection_session_id": detection_id,
            "treatment_recommendation_id": recommendation_id,
            "farmer_chat_id": farmer_chat_id,
        }

        def send() -> dict[str, Any]:
            assert self.base_url is not None
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(
                    f"{self.base_url}/notifications/telegram",
                    headers=self._headers(),
                    json=payload,
                )
                response.raise_for_status()
                return response.json()

        return self.retry_policy.run("backend.notifications.telegram", send)

