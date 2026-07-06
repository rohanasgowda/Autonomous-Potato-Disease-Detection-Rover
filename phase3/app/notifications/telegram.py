from __future__ import annotations

import logging
from typing import Any

import httpx

from phase3.app.schemas.detection import DetectionCreate
from phase3.app.schemas.inventory import InventoryCheckResponse
from phase3.app.schemas.pipeline import TelegramDeliveryResult
from phase3.app.schemas.treatment import TreatmentAgentOutput
from phase3.app.utils.retry import RetryPolicy


logger = logging.getLogger(__name__)


def _title(value: str) -> str:
    return value.replace("_", " ").strip().title()


def build_farmer_message(
    detection: DetectionCreate,
    treatment: TreatmentAgentOutput,
    inventory: InventoryCheckResponse | None,
) -> str:
    severity = (
        f"{_title(detection.severity.label)} "
        f"({detection.severity.infected_area_percent:.1f}% infected area)"
    )
    lines = [
        "Plant disease rover alert",
        "",
        f"Crop: {_title(detection.crop)}",
        f"Disease: {_title(detection.disease)}",
        f"Severity: {severity}",
        (
            "Grid position: "
            f"row {detection.grid_position.row_index}, plant {detection.grid_position.plant_index}"
        ),
        "",
        "Recommended treatment:",
    ]

    inventory_by_name: dict[str, Any] = {}
    if inventory is not None:
        inventory_by_name = {item.medicine_name.lower(): item for item in inventory.items}

    for recommendation in treatment.recommendations:
        required_quantity = recommendation.quantity_kg_per_acre
        inventory_item = inventory_by_name.get(recommendation.medicine_name.lower())
        lines.append(
            f"{recommendation.medicine_name} - {required_quantity:.2f} kg/acre"
        )
        if inventory_item is not None:
            availability = "Available" if inventory_item.is_available else "Not available"
            lines.append(f"Availability: {availability}")
            lines.append(
                f"Required quantity: {inventory_item.required_quantity_kg:.2f} kg"
            )
            lines.append(
                f"Estimated price: {inventory.currency} {inventory_item.estimated_total_price:.2f}"
            )
        else:
            lines.append("Availability: Not checked")
        lines.append(f"Application: {recommendation.application_frequency}")

    safety_items: list[str] = []
    for recommendation in treatment.recommendations:
        safety_items.extend(recommendation.safety_instructions)
    unique_safety = list(dict.fromkeys(safety_items))

    lines.extend(["", "Safety:"])
    lines.extend(unique_safety)
    lines.extend(["", f"Note: {treatment.disclaimer}"])
    return "\n".join(lines)


class TelegramClient:
    def __init__(
        self,
        bot_token: str | None,
        chat_id: str | None,
        base_url: str,
        timeout_seconds: float,
        retry_policy: RetryPolicy,
    ) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.retry_policy = retry_policy

    @property
    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def send_message(self, message: str) -> TelegramDeliveryResult:
        if not self.is_configured:
            return TelegramDeliveryResult(
                attempted=False,
                delivered=False,
                detail="Telegram credentials are not configured.",
                response_json=None,
            )

        def send() -> dict[str, Any]:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                assert self.bot_token is not None
                response = client.post(
                    f"{self.base_url}/bot{self.bot_token}/sendMessage",
                    json={"chat_id": self.chat_id, "text": message},
                )
                response.raise_for_status()
                return response.json()

        try:
            response_json = self.retry_policy.run("telegram.sendMessage", send)
        except Exception as exc:
            logger.exception("Telegram delivery failed", extra={"_error": str(exc)})
            return TelegramDeliveryResult(
                attempted=True,
                delivered=False,
                detail=str(exc),
                response_json=None,
            )
        return TelegramDeliveryResult(
            attempted=True,
            delivered=True,
            detail="Telegram message delivered.",
            response_json=response_json,
        )

