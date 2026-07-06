from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


SeverityLabel = Literal["healthy", "very_low", "low", "moderate", "high", "severe"]


class GridPosition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    row_index: int = Field(ge=0)
    plant_index: int = Field(ge=0)


class SeverityPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: SeverityLabel
    infected_area_percent: float = Field(ge=0, le=100)
    method: str = Field(min_length=1, max_length=100)


class ImagePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    local_path: str | None = Field(default=None, max_length=500)
    width: int | None = Field(default=None, gt=0)
    height: int | None = Field(default=None, gt=0)


class ModelPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=150)
    version: str = Field(min_length=1, max_length=50)
    runtime: str = Field(min_length=1, max_length=50)


class DetectionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(min_length=1, max_length=150)
    device_id: str = Field(min_length=1, max_length=150)
    timestamp: datetime
    grid_position: GridPosition
    crop: str = Field(min_length=1, max_length=100)
    disease: str = Field(min_length=1, max_length=150)
    confidence: float = Field(ge=0, le=1)
    severity: SeverityPayload
    image: ImagePayload
    model: ModelPayload


class DetectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: str
    device_id: str
    timestamp: datetime
    row_index: int
    plant_index: int
    crop: str
    disease: str
    confidence: float
    severity_label: str
    infected_area_percent: float
    image_path: str | None
    raw_detection_json: dict[str, Any]
