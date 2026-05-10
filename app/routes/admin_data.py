from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.environmental_data import EnvironmentalData
from app.models.neighborhood import Neighborhood
from app.models.route_history import RouteHistory
from app.models.user import User
from app.schemas.admin_data import (
    AirQualityUpdate,
    EnvironmentalDataUpdate,
    GreenAreaUpdate,
    NeighborhoodUpdate,
    NoiseUpdate,
    RouteHistoryUpdate,
)
from app.schemas.environmental_data import EnvironmentalDataResponse
from app.schemas.neighborhood import NeighborhoodResponse
from app.schemas.route_history import RouteHistoryResponse
from app.services.auth_service import get_current_active_user
from app.services.notification_service import create_air_quality_alert_if_needed

router = APIRouter(tags=["Admin Data"])


def get_current_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return current_user


@router.get("/admin/neighborhoods", response_model=list[NeighborhoodResponse])
def list_admin_neighborhoods(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)
) -> list[Neighborhood]:
    neighborhoods = db.scalars(select(Neighborhood)).all()
    return list(neighborhoods)


@router.patch("/admin/neighborhoods/{neighborhood_id}", response_model=NeighborhoodResponse)
def update_neighborhood(
    neighborhood_id: int,
    payload: NeighborhoodUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> Neighborhood:
    neighborhood = db.get(Neighborhood, neighborhood_id)
    if not neighborhood:
        raise HTTPException(status_code=404, detail="Neighborhood not found.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(neighborhood, field, value)

    db.commit()
    db.refresh(neighborhood)
    return neighborhood


@router.get("/admin/environmental-data", response_model=list[EnvironmentalDataResponse])
def list_admin_environmental_data(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)
) -> list[EnvironmentalData]:
    records = db.scalars(select(EnvironmentalData).order_by(desc(EnvironmentalData.created_at))).all()
    return list(records)


@router.patch(
    "/admin/environmental-data/{environmental_data_id}",
    response_model=EnvironmentalDataResponse,
)
def update_environmental_data(
    environmental_data_id: int,
    payload: EnvironmentalDataUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> EnvironmentalData:
    record = db.get(EnvironmentalData, environmental_data_id)
    if not record:
        raise HTTPException(status_code=404, detail="Environmental data not found.")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(record, field, value)

    db.commit()
    db.refresh(record)
    if "aqi" in update_data:
        create_air_quality_alert_if_needed(
            db,
            user_id=None,
            neighborhood_id=record.neighborhood_id,
            aqi=record.aqi,
        )
    return record


@router.patch(
    "/admin/environmental-data/{environmental_data_id}/air-quality",
    response_model=EnvironmentalDataResponse,
)
def update_air_quality_data(
    environmental_data_id: int,
    payload: AirQualityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> EnvironmentalData:
    record = db.get(EnvironmentalData, environmental_data_id)
    if not record:
        raise HTTPException(status_code=404, detail="Environmental data not found.")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(record, field, value)

    db.commit()
    db.refresh(record)
    if "aqi" in update_data:
        create_air_quality_alert_if_needed(
            db,
            user_id=None,
            neighborhood_id=record.neighborhood_id,
            aqi=record.aqi,
        )
    return record


@router.patch(
    "/admin/environmental-data/{environmental_data_id}/noise",
    response_model=EnvironmentalDataResponse,
)
def update_noise_data(
    environmental_data_id: int,
    payload: NoiseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> EnvironmentalData:
    record = db.get(EnvironmentalData, environmental_data_id)
    if not record:
        raise HTTPException(status_code=404, detail="Environmental data not found.")

    record.noise_level_dba = payload.noise_level_dba
    db.commit()
    db.refresh(record)
    return record


@router.patch(
    "/admin/environmental-data/{environmental_data_id}/green-area",
    response_model=EnvironmentalDataResponse,
)
def update_green_area_data(
    environmental_data_id: int,
    payload: GreenAreaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> EnvironmentalData:
    record = db.get(EnvironmentalData, environmental_data_id)
    if not record:
        raise HTTPException(status_code=404, detail="Environmental data not found.")

    record.green_area_ratio = payload.green_area_ratio
    db.commit()
    db.refresh(record)
    return record


@router.get("/admin/routes", response_model=list[RouteHistoryResponse])
def list_admin_routes(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)
) -> list[RouteHistory]:
    records = db.scalars(select(RouteHistory).order_by(desc(RouteHistory.created_at))).all()
    return list(records)


@router.patch("/admin/route-history/{route_history_id}", response_model=RouteHistoryResponse)
def update_route_history(
    route_history_id: int,
    payload: RouteHistoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> RouteHistory:
    record = db.get(RouteHistory, route_history_id)
    if not record:
        raise HTTPException(status_code=404, detail="Route history not found.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, field, value)

    db.commit()
    db.refresh(record)
    return record
