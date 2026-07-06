import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.models.detection import DetectionSession
from app.models.user import User
from app.schemas.detection import DetectionCreate, DetectionResponse


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/detections", tags=["detections"])


@router.post("", response_model=DetectionResponse, status_code=status.HTTP_201_CREATED)
def create_detection(
    payload: DetectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DetectionSession:
    detection = DetectionSession(
        session_id=payload.session_id,
        device_id=payload.device_id,
        timestamp=payload.timestamp,
        row_index=payload.grid_position.row_index,
        plant_index=payload.grid_position.plant_index,
        crop=payload.crop,
        disease=payload.disease,
        confidence=payload.confidence,
        severity_label=payload.severity.label,
        infected_area_percent=payload.severity.infected_area_percent,
        image_path=payload.image.local_path,
        raw_detection_json=payload.model_dump(mode="json"),
    )
    db.add(detection)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Detection session_id already exists.",
        ) from exc
    db.refresh(detection)
    logger.info(
        "Detection uploaded session_id=%s user=%s crop=%s disease=%s",
        detection.session_id,
        current_user.username,
        detection.crop,
        detection.disease,
    )
    return detection


@router.get("", response_model=list[DetectionResponse])
def list_detections(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[DetectionSession]:
    return (
        db.query(DetectionSession)
        .order_by(DetectionSession.timestamp.desc(), DetectionSession.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/{detection_id}", response_model=DetectionResponse)
def get_detection(
    detection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DetectionSession:
    detection = db.query(DetectionSession).filter(DetectionSession.id == detection_id).first()
    if detection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detection was not found.",
        )
    return detection
