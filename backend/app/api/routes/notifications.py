from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.models.user import User
from app.schemas.notification import (
    TelegramNotificationRequest,
    TelegramNotificationResponse,
)


router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("/telegram", response_model=TelegramNotificationResponse)
def telegram_notification_scaffold(
    payload: TelegramNotificationRequest,
    current_user: User = Depends(get_current_user),
) -> TelegramNotificationResponse:
    return TelegramNotificationResponse(
        status="not_implemented",
        detail=(
            "Telegram integration belongs to a later phase. "
            "This Phase 2 endpoint only preserves the documented API surface."
        ),
    )
