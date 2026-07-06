from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TreatmentRecommendationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    detection_session_id: int = Field(gt=0)
    model_provider: str = Field(default="openrouter", min_length=1, max_length=100)
    model_name: str = Field(min_length=1, max_length=150)
    raw_request_json: dict[str, Any]
    raw_response_json: dict[str, Any]


class TreatmentRecommendationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    detection_session_id: int
    model_provider: str
    model_name: str
    raw_request_json: dict[str, Any]
    raw_response_json: dict[str, Any]
    created_at: datetime
