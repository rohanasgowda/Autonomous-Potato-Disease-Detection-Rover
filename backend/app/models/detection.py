from sqlalchemy import Column, DateTime, Float, Index, Integer, JSON, String

from app.db.session import Base


class DetectionSession(Base):
    __tablename__ = "detection_sessions"
    __table_args__ = (
        Index("ix_detection_sessions_crop_disease", "crop", "disease"),
        Index("ix_detection_sessions_grid", "row_index", "plant_index"),
    )

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, nullable=False, index=True)
    device_id = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    row_index = Column(Integer, nullable=False)
    plant_index = Column(Integer, nullable=False)
    crop = Column(String, nullable=False, index=True)
    disease = Column(String, nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    severity_label = Column(String, nullable=False, index=True)
    infected_area_percent = Column(Float, nullable=False)
    image_path = Column(String, nullable=True)
    raw_detection_json = Column(JSON, nullable=False)
