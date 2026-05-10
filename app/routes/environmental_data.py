from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.environmental_data import EnvironmentalData
from app.models.neighborhood import Neighborhood
from app.schemas.environmental_data import EnvironmentalDataCreate, EnvironmentalDataResponse
from app.services.notification_service import create_air_quality_alert_if_needed

router = APIRouter(prefix="/environmental-data", tags=["Environmental Data"])


@router.post("", response_model=EnvironmentalDataResponse, status_code=201)
def create_environmental_data(
    payload: EnvironmentalDataCreate, db: Session = Depends(get_db)
) -> EnvironmentalData:
    neighborhood = db.get(Neighborhood, payload.neighborhood_id)
    if not neighborhood:
        raise HTTPException(status_code=404, detail="Neighborhood not found.")

    record = EnvironmentalData(**payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    create_air_quality_alert_if_needed(
        db,
        user_id=None,
        neighborhood_id=record.neighborhood_id,
        aqi=record.aqi,
    )
    return record


@router.get("/{neighborhood_id}", response_model=list[EnvironmentalDataResponse])
def get_environmental_data_by_neighborhood(
    neighborhood_id: int, db: Session = Depends(get_db)
) -> list[EnvironmentalData]:
    records = db.scalars(
        select(EnvironmentalData)
        .where(EnvironmentalData.neighborhood_id == neighborhood_id)
        .order_by(desc(EnvironmentalData.created_at))
    ).all()
    return list(records)
