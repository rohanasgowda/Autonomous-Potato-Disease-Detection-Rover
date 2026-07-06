import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.models.detection import DetectionSession
from app.models.recommendation import TreatmentRecommendation
from app.models.user import User
from app.schemas.recommendation import (
    TreatmentRecommendationCreate,
    TreatmentRecommendationResponse,
)


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("", response_model=TreatmentRecommendationResponse, status_code=status.HTTP_201_CREATED)
def create_recommendation(
    payload: TreatmentRecommendationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TreatmentRecommendation:
    detection = (
        db.query(DetectionSession)
        .filter(DetectionSession.id == payload.detection_session_id)
        .first()
    )
    if detection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detection session was not found.",
        )

    recommendation = TreatmentRecommendation(**payload.model_dump(mode="json"))
    db.add(recommendation)
    db.commit()
    db.refresh(recommendation)
    logger.info(
        "Treatment recommendation stored id=%s detection_session_id=%s user=%s",
        recommendation.id,
        recommendation.detection_session_id,
        current_user.username,
    )
    return recommendation


@router.get("/{recommendation_id}", response_model=TreatmentRecommendationResponse)
def get_recommendation(
    recommendation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TreatmentRecommendation:
    recommendation = (
        db.query(TreatmentRecommendation)
        .filter(TreatmentRecommendation.id == recommendation_id)
        .first()
    )
    if recommendation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Treatment recommendation was not found.",
        )
    return recommendation
