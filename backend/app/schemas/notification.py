from pydantic import BaseModel, ConfigDict, Field


class TelegramNotificationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    detection_session_id: int = Field(gt=0)
    treatment_recommendation_id: int | None = Field(default=None, gt=0)
    farmer_chat_id: str | None = Field(default=None, max_length=150)


class TelegramNotificationResponse(BaseModel):
    status: str
    detail: str
