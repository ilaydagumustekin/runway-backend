from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.neighborhood import Neighborhood
from app.models.noise_measurement import NoiseMeasurement
from app.schemas.noise_measurement import NoiseMeasurementCreate, NoiseMeasurementResponse

router = APIRouter(prefix="/noise-measurements", tags=["Noise Measurements"])


@router.post("", response_model=NoiseMeasurementResponse, status_code=201)
def create_noise_measurement(
    payload: NoiseMeasurementCreate, db: Session = Depends(get_db)
) -> NoiseMeasurement:
    neighborhood = db.get(Neighborhood, payload.neighborhood_id)
    if not neighborhood:
        raise HTTPException(status_code=404, detail="Neighborhood not found.")

    record = NoiseMeasurement(**payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
