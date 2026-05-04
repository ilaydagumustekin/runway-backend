from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardHomeResponse
from app.services.auth_service import get_current_active_user
from app.services.dashboard_service import build_dashboard_home

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/home", response_model=DashboardHomeResponse)
def get_dashboard_home(
    neighborhood_id: int | None = Query(default=None),
    latitude: float | None = Query(default=None),
    longitude: float | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DashboardHomeResponse:
    dashboard = build_dashboard_home(
        db,
        current_user,
        neighborhood_id=neighborhood_id,
        latitude=latitude,
        longitude=longitude,
    )
    if not dashboard:
        raise HTTPException(status_code=404, detail="No neighborhoods found for dashboard.")
    return dashboard
