from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.routes import RouteRecommendRequest, RouteRecommendResponse
from app.services.route_service import recommend_route

router = APIRouter(prefix="/routes", tags=["Routes"])


@router.post("/recommend", response_model=RouteRecommendResponse)
def recommend(
    payload: RouteRecommendRequest,
    db: Session = Depends(get_db)
) -> RouteRecommendResponse:
    return recommend_route(db, payload)
