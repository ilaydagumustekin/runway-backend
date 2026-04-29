from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.environmental_data import EnvironmentalData
from app.schemas.myki import MYKIResponse
from app.services.myki_service import calculate_myki_from_environmental_data

router = APIRouter(prefix="/myki", tags=["MYKI"])


@router.get("/{neighborhood_id}", response_model=MYKIResponse)
def get_myki(neighborhood_id: int, db: Session = Depends(get_db)) -> MYKIResponse:
    latest_record = db.scalar(
        select(EnvironmentalData)
        .where(EnvironmentalData.neighborhood_id == neighborhood_id)
        .order_by(desc(EnvironmentalData.created_at))
    )

    if not latest_record:
        raise HTTPException(
            status_code=404, detail="No environmental data found for this neighborhood."
        )

    score, category = calculate_myki_from_environmental_data(latest_record)
    return MYKIResponse(neighborhood_id=neighborhood_id, score=score, category=category)
