from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class InventoryItemBase(BaseModel):
    medicine_name: str = Field(min_length=1, max_length=200)
    stock_quantity_kg: float = Field(ge=0)
    price_per_kg: float = Field(ge=0)
    expiry_date: date


class InventoryItemCreate(InventoryItemBase):
    model_config = ConfigDict(extra="forbid")


class InventoryItemUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    medicine_name: str | None = Field(default=None, min_length=1, max_length=200)
    stock_quantity_kg: float | None = Field(default=None, ge=0)
    price_per_kg: float | None = Field(default=None, ge=0)
    expiry_date: date | None = None


class InventoryItemResponse(InventoryItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class InventoryCheckRequestItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    medicine_name: str = Field(min_length=1, max_length=200)
    required_quantity_kg: float = Field(gt=0)


class InventoryCheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str | None = Field(default=None, max_length=150)
    vendor_id: str = Field(default="vendor_001", min_length=1, max_length=100)
    treatment_recommendation_id: int | None = Field(default=None, gt=0)
    items: list[InventoryCheckRequestItem] = Field(min_length=1)


class InventoryCheckResponseItem(BaseModel):
    medicine_name: str
    required_quantity_kg: float
    available_quantity_kg: float
    is_available: bool
    unit_price: float | None
    estimated_total_price: float
    expiry_date: date | None


class InventoryCheckResponse(BaseModel):
    session_id: str | None
    vendor_id: str
    items: list[InventoryCheckResponseItem]
    total_estimated_price: float
    currency: str = "INR"
