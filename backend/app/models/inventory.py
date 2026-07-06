from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship

from app.db.session import Base


class InventoryItem(Base):
    __tablename__ = "inventory_items"
    __table_args__ = (Index("ix_inventory_items_medicine_name", "medicine_name", unique=True),)

    id = Column(Integer, primary_key=True, index=True)
    medicine_name = Column(String, nullable=False)
    stock_quantity_kg = Column(Float, nullable=False)
    price_per_kg = Column(Float, nullable=False)
    expiry_date = Column(Date, nullable=False, index=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class InventoryCheck(Base):
    __tablename__ = "inventory_checks"

    id = Column(Integer, primary_key=True, index=True)
    treatment_recommendation_id = Column(
        Integer,
        ForeignKey("treatment_recommendations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    medicine_name = Column(String, nullable=False, index=True)
    required_quantity_kg = Column(Float, nullable=False)
    available_quantity_kg = Column(Float, nullable=False)
    is_available = Column(Boolean, nullable=False)
    estimated_total_price = Column(Float, nullable=False)
    checked_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    treatment_recommendation = relationship("TreatmentRecommendation")
