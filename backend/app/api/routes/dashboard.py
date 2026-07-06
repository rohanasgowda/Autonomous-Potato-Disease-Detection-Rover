from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.models.detection import DetectionSession
from app.models.inventory import InventoryItem
from app.models.user import User
from app.schemas.dashboard import (
    DashboardSummary,
    LatestDetectionSummary,
    LowStockMedicine,
)


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardSummary:
    settings = get_settings()
    total_detections = db.query(func.count(DetectionSession.id)).scalar() or 0
    healthy_plants_count = (
        db.query(func.count(DetectionSession.id))
        .filter(
            (func.lower(DetectionSession.disease) == "healthy")
            | (func.lower(DetectionSession.severity_label) == "healthy")
        )
        .scalar()
        or 0
    )
    high_severity_plants_count = (
        db.query(func.count(DetectionSession.id))
        .filter(func.lower(DetectionSession.severity_label).in_(["high", "severe"]))
        .scalar()
        or 0
    )
    low_stock_items = (
        db.query(InventoryItem)
        .filter(InventoryItem.stock_quantity_kg <= settings.LOW_STOCK_THRESHOLD_KG)
        .order_by(InventoryItem.stock_quantity_kg.asc(), InventoryItem.medicine_name.asc())
        .limit(20)
        .all()
    )
    latest_detections = (
        db.query(DetectionSession)
        .order_by(DetectionSession.timestamp.desc(), DetectionSession.id.desc())
        .limit(5)
        .all()
    )

    return DashboardSummary(
        total_detections=total_detections,
        diseased_plants_count=total_detections - healthy_plants_count,
        healthy_plants_count=healthy_plants_count,
        high_severity_plants_count=high_severity_plants_count,
        low_stock_medicines=[
            LowStockMedicine(
                id=item.id,
                medicine_name=item.medicine_name,
                stock_quantity_kg=item.stock_quantity_kg,
                expiry_date=item.expiry_date,
            )
            for item in low_stock_items
        ],
        latest_detections=[
            LatestDetectionSummary(
                id=detection.id,
                session_id=detection.session_id,
                timestamp=detection.timestamp,
                crop=detection.crop,
                disease=detection.disease,
                severity_label=detection.severity_label,
                row_index=detection.row_index,
                plant_index=detection.plant_index,
            )
            for detection in latest_detections
        ],
    )
