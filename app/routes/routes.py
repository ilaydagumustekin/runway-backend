from fastapi import APIRouter

from app.schemas.routes import RouteRecommendRequest, RouteRecommendResponse
from app.services.route_service import recommend_route

router = APIRouter(prefix="/routes", tags=["Routes"])


@router.post("/recommend", response_model=RouteRecommendResponse)
def recommend(payload: RouteRecommendRequest) -> RouteRecommendResponse:
    return recommend_route(payload)
