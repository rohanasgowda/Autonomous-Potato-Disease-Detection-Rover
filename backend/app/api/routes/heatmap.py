from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.detection import DetectionSession

router = APIRouter(prefix="/heatmap", tags=["Heatmap"])


@router.get("/")
def get_heatmap(db: Session = Depends(get_db)):

    detections = db.query(DetectionSession).all()

    # Fixed field size
    rows = 2
    cols = 8

    grid = [[0 for _ in range(cols)] for _ in range(rows)]
    details = {}

    for d in detections:

        # Ignore any detections outside the field
        if d.row_index >= rows or d.plant_index >= cols:
            continue

        grid[d.row_index][d.plant_index] = d.infected_area_percent

        details[f"{d.row_index}_{d.plant_index}"] = {
            "disease": d.disease,
            "confidence": d.confidence,
            "severity": d.infected_area_percent,
            "image": d.image_path
        }

    return {
        "rows": rows,
        "cols": cols,
        "grid": grid,
        "details": details
    }


@router.post("/reset")
def reset_heatmap(db: Session = Depends(get_db)):

    db.query(DetectionSession).delete()

    db.commit()

    return {
        "message": "Heatmap reset successful"
    }