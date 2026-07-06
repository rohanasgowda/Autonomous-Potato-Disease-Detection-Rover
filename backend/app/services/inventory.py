from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.inventory import InventoryCheck, InventoryItem
from app.models.recommendation import TreatmentRecommendation
from app.schemas.inventory import (
    InventoryCheckRequest,
    InventoryCheckResponse,
    InventoryCheckResponseItem,
)


def normalize_medicine_name(name: str) -> str:
    return " ".join(name.strip().lower().split())


def find_inventory_item_by_name(db: Session, medicine_name: str) -> InventoryItem | None:
    normalized_name = normalize_medicine_name(medicine_name)
    return (
        db.query(InventoryItem)
        .filter(func.lower(func.trim(InventoryItem.medicine_name)) == normalized_name)
        .first()
    )


def check_inventory(db: Session, payload: InventoryCheckRequest) -> InventoryCheckResponse:
    settings = get_settings()
    if payload.treatment_recommendation_id is not None:
        recommendation = (
            db.query(TreatmentRecommendation)
            .filter(TreatmentRecommendation.id == payload.treatment_recommendation_id)
            .first()
        )
        if recommendation is None:
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Treatment recommendation was not found.",
            )

    response_items: list[InventoryCheckResponseItem] = []
    total_estimated_price = 0.0

    for requested_item in payload.items:
        inventory_item = find_inventory_item_by_name(db, requested_item.medicine_name)
        available_quantity = inventory_item.stock_quantity_kg if inventory_item else 0.0
        unit_price = inventory_item.price_per_kg if inventory_item else None
        estimated_total_price = (
            round(requested_item.required_quantity_kg * unit_price, 2)
            if unit_price is not None
            else 0.0
        )
        is_available = inventory_item is not None and available_quantity >= requested_item.required_quantity_kg

        total_estimated_price += estimated_total_price
        response_items.append(
            InventoryCheckResponseItem(
                medicine_name=requested_item.medicine_name,
                required_quantity_kg=requested_item.required_quantity_kg,
                available_quantity_kg=available_quantity,
                is_available=is_available,
                unit_price=unit_price,
                estimated_total_price=estimated_total_price,
                expiry_date=inventory_item.expiry_date if inventory_item else None,
            )
        )

        db.add(
            InventoryCheck(
                treatment_recommendation_id=payload.treatment_recommendation_id,
                medicine_name=requested_item.medicine_name,
                required_quantity_kg=requested_item.required_quantity_kg,
                available_quantity_kg=available_quantity,
                is_available=is_available,
                estimated_total_price=estimated_total_price,
            )
        )

    db.commit()
    return InventoryCheckResponse(
        session_id=payload.session_id,
        vendor_id=payload.vendor_id,
        items=response_items,
        total_estimated_price=round(total_estimated_price, 2),
        currency=settings.CURRENCY,
    )
