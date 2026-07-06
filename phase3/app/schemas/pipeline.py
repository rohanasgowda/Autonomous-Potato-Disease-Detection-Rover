from typing import Any

from pydantic import BaseModel, ConfigDict

from phase3.app.schemas.inventory import InventoryCheckResponse
from phase3.app.schemas.treatment import TreatmentAgentOutput


class BackendSyncResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    detection_id: int | None = None
    recommendation_id: int | None = None
    inventory: InventoryCheckResponse | None = None


class TelegramDeliveryResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    attempted: bool
    delivered: bool
    detail: str
    response_json: dict[str, Any] | None = None


class TreatmentPipelineResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    treatment: TreatmentAgentOutput
    backend: BackendSyncResult
    telegram: TelegramDeliveryResult | None = None

