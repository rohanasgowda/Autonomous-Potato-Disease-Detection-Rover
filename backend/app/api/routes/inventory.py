import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_roles
from app.db.session import get_db
from app.models.inventory import InventoryItem
from app.models.user import User
from app.schemas.inventory import (
    InventoryCheckRequest,
    InventoryCheckResponse,
    InventoryItemCreate,
    InventoryItemResponse,
    InventoryItemUpdate,
)
from app.services.inventory import check_inventory, normalize_medicine_name


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/inventory", tags=["inventory"])


def ensure_unique_medicine_name(
    db: Session,
    medicine_name: str,
    current_item_id: int | None = None,
) -> None:
    normalized_name = normalize_medicine_name(medicine_name)
    query = db.query(InventoryItem).filter(
        func.lower(func.trim(InventoryItem.medicine_name)) == normalized_name
    )
    if current_item_id is not None:
        query = query.filter(InventoryItem.id != current_item_id)
    if query.first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Inventory medicine_name already exists.",
        )


@router.post("/check", response_model=InventoryCheckResponse)
def inventory_check(
    payload: InventoryCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InventoryCheckResponse:
    response = check_inventory(db, payload)
    logger.info(
        "Inventory check user=%s session_id=%s items=%s",
        current_user.username,
        payload.session_id,
        len(payload.items),
    )
    return response


@router.get("", response_model=list[InventoryItemResponse])
def list_inventory(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[InventoryItem]:
    return db.query(InventoryItem).order_by(InventoryItem.medicine_name.asc()).all()


@router.post("", response_model=InventoryItemResponse, status_code=status.HTTP_201_CREATED)
def create_inventory_item(
    payload: InventoryItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "vendor")),
) -> InventoryItem:
    ensure_unique_medicine_name(db, payload.medicine_name)
    item = InventoryItem(**payload.model_dump())
    db.add(item)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Inventory item could not be created due to a uniqueness conflict.",
        ) from exc
    db.refresh(item)
    logger.info("Inventory item created id=%s user=%s", item.id, current_user.username)
    return item


@router.put("/{item_id}", response_model=InventoryItemResponse)
def update_inventory_item(
    item_id: int,
    payload: InventoryItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "vendor")),
) -> InventoryItem:
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item was not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    if "medicine_name" in update_data:
        ensure_unique_medicine_name(db, update_data["medicine_name"], current_item_id=item.id)

    for field, value in update_data.items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    logger.info("Inventory item updated id=%s user=%s", item.id, current_user.username)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inventory_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "vendor")),
) -> Response:
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item was not found.",
        )
    db.delete(item)
    db.commit()
    logger.info("Inventory item deleted id=%s user=%s", item_id, current_user.username)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
