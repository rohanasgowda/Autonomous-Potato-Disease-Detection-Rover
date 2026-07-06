from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from phase3.app.clients.openrouter import OpenRouterClient
from phase3.app.config.settings import Settings as Phase3Settings
from phase3.app.integrations.backend import BackendClient
from phase3.app.main import build_pipeline
from phase3.app.notifications.telegram import TelegramClient, build_farmer_message
from phase3.app.schemas.detection import DetectionCreate
from phase3.app.schemas.pipeline import BackendSyncResult, TelegramDeliveryResult
from phase3.app.services.transformer import (
    detection_to_treatment_input,
    treatment_to_inventory_request,
)
from phase4.app.config import Phase4Config
from phase4.app.inference import build_detection_payload, run_tflite_prediction

from phase6.camera import CameraCapture, CameraCaptureError, generate_session_id
from phase6.grid import GridMovementController, NoOpGridMovementController
from phase6.storage import LocalSessionStore


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class WorkflowResult:
    session_id: str
    image_path: str | None
    detection_json: dict[str, Any] | None
    treatment_json: dict[str, Any] | None
    backend: BackendSyncResult
    telegram: TelegramDeliveryResult | None
    sync_status: str
    errors: list[dict[str, str]]


class Phase6WorkflowController:
    def __init__(
        self,
        *,
        camera: CameraCapture,
        store: LocalSessionStore,
        phase4_config: Phase4Config,
        model_path: str | Path,
        labels_path: str | Path,
        openrouter_client: OpenRouterClient,
        backend_client: BackendClient,
        telegram_client: TelegramClient,
        openrouter_model_name: str,
        backend_vendor_id: str,
        grid_controller: GridMovementController | None = None,
    ) -> None:
        self.camera = camera
        self.store = store
        self.phase4_config = phase4_config
        self.model_path = Path(model_path)
        self.labels_path = Path(labels_path)
        self.openrouter_client = openrouter_client
        self.backend_client = backend_client
        self.telegram_client = telegram_client
        self.openrouter_model_name = openrouter_model_name
        self.backend_vendor_id = backend_vendor_id
        self.grid_controller = grid_controller or NoOpGridMovementController()

    @classmethod
    def from_settings(
        cls,
        *,
        phase3_settings: Phase3Settings,
        phase4_config: Phase4Config,
        model_path: str | Path,
        labels_path: str | Path,
        capture_dir: str | Path,
        local_db_path: str | Path,
        camera_index: int = 0,
        camera_warmup_seconds: float = 0.2,
    ) -> "Phase6WorkflowController":
        pipeline = build_pipeline(phase3_settings)
        return cls(
            camera=CameraCapture(capture_dir, camera_index, camera_warmup_seconds),
            store=LocalSessionStore(local_db_path, phase4_config.max_local_sessions),
            phase4_config=phase4_config,
            model_path=model_path,
            labels_path=labels_path,
            openrouter_client=pipeline.openrouter_client,
            backend_client=pipeline.backend_client,
            telegram_client=pipeline.telegram_client,
            openrouter_model_name=phase3_settings.openrouter_model,
            backend_vendor_id=phase3_settings.backend_vendor_id,
            grid_controller=NoOpGridMovementController(),
        )

    def run_scan(
        self,
        *,
        farm_size_acres: float,
        number_of_plants: int,
        country: str = "India",
        language: str = "English",
        row_index: int = 0,
        plant_index: int = 0,
        source_image: str | Path | None = None,
        sync_backend: bool = True,
        send_telegram: bool = True,
    ) -> WorkflowResult:
        session_id = generate_session_id()
        errors: list[dict[str, str]] = []
        detection_payload: dict[str, Any] | None = None
        treatment_json: dict[str, Any] | None = None
        backend_result = BackendSyncResult()
        telegram_result: TelegramDeliveryResult | None = None
        image_path: Path | None = None

        self.store.create_session(session_id)
        try:
            self.grid_controller.move_to_grid_position(row_index, plant_index)
            self.grid_controller.stop()
        except Exception as exc:
            return self._fail(session_id, None, "grid_movement_failed", exc, errors)

        try:
            capture = self.camera.capture(session_id, source_image=source_image)
            image_path = capture.image_path
            self.store.update_session(
                session_id,
                image_path=image_path,
                sync_status="captured",
            )
        except CameraCaptureError as exc:
            return self._fail(session_id, None, "camera_failed", exc, errors)

        try:
            prediction = run_tflite_prediction(
                model_path=self.model_path,
                image_path=image_path,
                labels_path=self.labels_path,
                image_size=self.phase4_config.image_size_hw,
            )
            detection_payload = build_detection_payload(
                prediction=prediction,
                image_path=image_path,
                model_name=self.phase4_config.model_name,
                model_version=self.phase4_config.model_version,
                device_id=self.phase4_config.device_id,
                row_index=row_index,
                plant_index=plant_index,
                session_id=session_id,
            )
            self.store.update_session(
                session_id,
                detection_json=detection_payload,
                sync_status="detected",
            )
            detection = _validated_detection(detection_payload)
        except Exception as exc:
            return self._fail(session_id, image_path, "inference_failed", exc, errors)

        try:
            agent_input = detection_to_treatment_input(
                detection=detection,
                farm_size_acres=farm_size_acres,
                number_of_plants=number_of_plants,
                country=country,
                language=language,
            )
            treatment, _, _ = self.openrouter_client.generate_treatment(agent_input)
            treatment_json = treatment.model_dump(mode="json")
            self.store.update_session(
                session_id,
                treatment_json=treatment_json,
                sync_status="treated",
            )
        except Exception as exc:
            return self._fail(session_id, image_path, "treatment_failed", exc, errors)

        if sync_backend:
            try:
                if self.backend_client.is_configured:
                    detection_response = self.backend_client.upload_detection(detection)
                    detection_id = detection_response["id"]
                    recommendation_response = self.backend_client.upload_recommendation(
                        detection_id=detection_id,
                        model_name=self.openrouter_model_name,
                        raw_request=agent_input,
                        raw_response=treatment,
                    )
                    recommendation_id = recommendation_response["id"]
                    inventory_request = treatment_to_inventory_request(
                        treatment=treatment,
                        agent_input=agent_input,
                        session_id=session_id,
                        vendor_id=self.backend_vendor_id,
                        treatment_recommendation_id=recommendation_id,
                    )
                    inventory = self.backend_client.check_inventory(inventory_request)
                    backend_result = BackendSyncResult(
                        detection_id=detection_id,
                        recommendation_id=recommendation_id,
                        inventory=inventory,
                    )
                    self.store.update_session(
                        session_id,
                        backend_json={
                            "detection": detection_response,
                            "recommendation": recommendation_response,
                        },
                        inventory_json=inventory.model_dump(mode="json"),
                        sync_status="backend_synced",
                    )
                else:
                    self.store.update_session(session_id, sync_status="backend_skipped")
            except Exception as exc:
                self._record_error(session_id, "backend_failed", exc, errors)

        if send_telegram:
            try:
                message = build_farmer_message(detection, treatment, backend_result.inventory)
                telegram_result = self.telegram_client.send_message(message)
                self.store.update_session(
                    session_id,
                    telegram_json=telegram_result.model_dump(mode="json"),
                    sync_status=_final_status(errors, telegram_result.delivered),
                )
                if not telegram_result.delivered:
                    errors.append({"stage": "telegram_failed", "message": telegram_result.detail})
            except Exception as exc:
                self._record_error(session_id, "telegram_failed", exc, errors)

        if not send_telegram:
            self.store.update_session(
                session_id,
                sync_status="completed_with_errors" if errors else "completed",
            )

        row = self.store.get_session(session_id) or {}
        return WorkflowResult(
            session_id=session_id,
            image_path=str(image_path) if image_path is not None else None,
            detection_json=detection_payload,
            treatment_json=treatment_json,
            backend=backend_result,
            telegram=telegram_result,
            sync_status=row.get("sync_status", "unknown"),
            errors=errors,
        )

    def _fail(
        self,
        session_id: str,
        image_path: Path | None,
        status: str,
        exc: Exception,
        errors: list[dict[str, str]],
    ) -> WorkflowResult:
        self._record_error(session_id, status, exc, errors)
        return WorkflowResult(
            session_id=session_id,
            image_path=str(image_path) if image_path is not None else None,
            detection_json=None,
            treatment_json=None,
            backend=BackendSyncResult(),
            telegram=None,
            sync_status=status,
            errors=errors,
        )

    def _record_error(
        self,
        session_id: str,
        stage: str,
        exc: Exception,
        errors: list[dict[str, str]],
    ) -> None:
        LOGGER.exception("Phase 6 workflow stage failed", extra={"_stage": stage, "_session_id": session_id})
        errors.append({"stage": stage, "message": str(exc)})
        self.store.update_session(
            session_id,
            sync_status=stage,
            error_json=errors,
        )


def _validated_detection(payload: dict[str, Any]) -> DetectionCreate:
    candidate = dict(payload)
    candidate.pop("runtime", None)
    try:
        return DetectionCreate.model_validate(candidate)
    except ValidationError:
        LOGGER.exception("Detection JSON did not match the existing schema")
        raise


def _final_status(errors: list[dict[str, str]], telegram_delivered: bool) -> str:
    if not telegram_delivered:
        return "telegram_failed"
    if errors:
        return "completed_with_errors"
    return "completed"
