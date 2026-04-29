from fastapi import APIRouter

from app.services.air_quality_prediction_service import predict_air_quality_for_next_hours
from app.services.green_area_analysis_service import analyze_green_area_placeholder
from app.services.tuik_validation_service import validate_with_tuik_placeholder

router = APIRouter(prefix="/integrations", tags=["Future Integrations"])


@router.get("/air-quality-prediction/{neighborhood_id}")
def air_quality_prediction(neighborhood_id: int, hours: int = 24) -> dict:
    return predict_air_quality_for_next_hours(neighborhood_id=neighborhood_id, hours=hours)


@router.get("/green-area-analysis/{neighborhood_id}")
def green_area_analysis(neighborhood_id: int) -> dict:
    return analyze_green_area_placeholder(neighborhood_id)


@router.get("/tuik-validation/{neighborhood_id}")
def tuik_validation(neighborhood_id: int) -> dict:
    return validate_with_tuik_placeholder(neighborhood_id)
