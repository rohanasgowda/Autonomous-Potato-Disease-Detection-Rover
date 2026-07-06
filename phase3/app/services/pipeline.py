from __future__ import annotations

import logging
from uuid import uuid4

from pydantic import ValidationError

from phase3.app.clients.openrouter import OpenRouterClient
from phase3.app.integrations.backend import BackendClient
from phase3.app.notifications.telegram import TelegramClient, build_farmer_message
from phase3.app.schemas.detection import DetectionCreate
from phase3.app.schemas.pipeline import BackendSyncResult, TreatmentPipelineResult
from phase3.app.services.transformer import (
    detection_to_treatment_input,
    treatment_to_inventory_request,
)
from phase3.app.storage.audit_store import AuditStore


logger = logging.getLogger(__name__)


class TreatmentPipeline:
    def __init__(
        self,
        openrouter_client: OpenRouterClient,
        backend_client: BackendClient,
        telegram_client: TelegramClient,
        audit_store: AuditStore,
        model_name: str,
        backend_vendor_id: str,
    ) -> None:
        self.openrouter_client = openrouter_client
        self.backend_client = backend_client
        self.telegram_client = telegram_client
        self.audit_store = audit_store
        self.model_name = model_name
        self.backend_vendor_id = backend_vendor_id

    def run(
        self,
        detection_payload: dict,
        farm_size_acres: float,
        number_of_plants: int,
        country: str = "India",
        language: str = "English",
        sync_backend: bool = True,
        send_telegram: bool = True,
    ) -> TreatmentPipelineResult:
        run_id = str(uuid4())
        try:
            detection_payload.pop("runtime", None)
            detection = DetectionCreate.model_validate(detection_payload)
            agent_input = detection_to_treatment_input(
                detection=detection,
                farm_size_acres=farm_size_acres,
                number_of_plants=number_of_plants,
                country=country,
                language=language,
            )
        except ValidationError as exc:
            logger.exception("Input validation failed", extra={"_run_id": run_id})
            raise

        self.audit_store.create_run(
            run_id=run_id,
            model_name=self.model_name,
            detection_json=detection.model_dump(mode="json"),
            agent_input_json=agent_input.model_dump(mode="json"),
        )

        try:
            treatment, openrouter_request, raw_response = self.openrouter_client.generate_treatment(
                agent_input
            )
            self.audit_store.update_run(
                run_id,
                validation_status="openrouter_validated",
                openrouter_request_json=openrouter_request,
                raw_response_json=raw_response,
                parsed_response_json=treatment.model_dump(mode="json"),
            )
        except Exception as exc:
            self.audit_store.update_run(
                run_id,
                validation_status="openrouter_failed",
                error_message=str(exc),
            )
            raise

        backend_result = BackendSyncResult()
        if sync_backend and self.backend_client.is_configured:
            try:
                detection_response = self.backend_client.upload_detection(detection)
                detection_id = detection_response["id"]
                recommendation_response = self.backend_client.upload_recommendation(
                    detection_id=detection_id,
                    model_name=self.model_name,
                    raw_request=agent_input,
                    raw_response=treatment,
                )
                recommendation_id = recommendation_response["id"]
                inventory_request = treatment_to_inventory_request(
                    treatment=treatment,
                    agent_input=agent_input,
                    session_id=detection.session_id,
                    vendor_id=self.backend_vendor_id,
                    treatment_recommendation_id=recommendation_id,
                )
                inventory = self.backend_client.check_inventory(inventory_request)
                backend_result = BackendSyncResult(
                    detection_id=detection_id,
                    recommendation_id=recommendation_id,
                    inventory=inventory,
                )
                self.audit_store.update_run(
                    run_id,
                    backend_result_json={
                        "detection": detection_response,
                        "recommendation": recommendation_response,
                    },
                    inventory_result_json=inventory.model_dump(mode="json"),
                )
            except Exception as exc:
                self.audit_store.update_run(
                    run_id,
                    validation_status="backend_sync_failed",
                    error_message=str(exc),
                )
                logger.exception("Backend sync failed", extra={"_run_id": run_id})
                raise
        elif sync_backend:
            logger.warning(
                "Backend sync requested but backend credentials are not configured",
                extra={"_run_id": run_id},
            )

        telegram_result = None
        if send_telegram:
            message = build_farmer_message(detection, treatment, backend_result.inventory)
            telegram_result = self.telegram_client.send_message(message)
            self.audit_store.update_run(
                run_id,
                telegram_result_json=telegram_result.model_dump(mode="json"),
            )

        self.audit_store.update_run(run_id, validation_status="completed")
        return TreatmentPipelineResult(
            run_id=run_id,
            treatment=treatment,
            backend=backend_result,
            telegram=telegram_result,
        )

