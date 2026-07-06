from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from app.db.session import Base


class TreatmentRecommendation(Base):
    __tablename__ = "treatment_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    detection_session_id = Column(
        Integer,
        ForeignKey("detection_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    model_provider = Column(String, nullable=False, default="openrouter")
    model_name = Column(String, nullable=False)
    raw_request_json = Column(JSON, nullable=False)
    raw_response_json = Column(JSON, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    detection_session = relationship("DetectionSession")
