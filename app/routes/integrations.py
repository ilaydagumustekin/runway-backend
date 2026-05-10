from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.neighborhood import Neighborhood
from app.services.air_quality_prediction_service import predict_air_quality_for_next_hours
from app.services.green_area_analysis_service import analyze_neighborhood_green_area
from app.services.tuik_validation_service import validate_neighborhood_data

router = APIRouter(prefix="/integrations", tags=["Core Environmental Intelligence"])


@router.get("/air-quality-prediction/{neighborhood_id}")
def air_quality_prediction(neighborhood_id: int, hours: int = 24) -> dict:
    return predict_air_quality_for_next_hours(neighborhood_id=neighborhood_id, hours=hours)


@router.get("/green-area-analysis/{neighborhood_id}")
def green_area_analysis(neighborhood_id: int, db: Session = Depends(get_db)) -> dict:
    neighborhood = db.get(Neighborhood, neighborhood_id)
    if not neighborhood:
        return {"status": "error", "message": "Neighborhood not found."}
    return analyze_neighborhood_green_area(neighborhood)


@router.get("/tuik-validation/{neighborhood_id}")
def tuik_validation(neighborhood_id: int, db: Session = Depends(get_db)) -> dict:
    neighborhood = db.get(Neighborhood, neighborhood_id)
    if not neighborhood:
        return {"status": "error", "message": "Neighborhood not found."}
    return validate_neighborhood_data(db, neighborhood)
