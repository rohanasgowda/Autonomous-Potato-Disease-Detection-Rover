from datetime import date, datetime

from pydantic import BaseModel


class LatestDetectionSummary(BaseModel):
    id: int
    session_id: str
    timestamp: datetime
    crop: str
    disease: str
    severity_label: str
    row_index: int
    plant_index: int


class LowStockMedicine(BaseModel):
    id: int
    medicine_name: str
    stock_quantity_kg: float
    expiry_date: date


class DashboardSummary(BaseModel):
    total_detections: int
    diseased_plants_count: int
    healthy_plants_count: int
    high_severity_plants_count: int
    low_stock_medicines: list[LowStockMedicine]
    latest_detections: list[LatestDetectionSummary]
