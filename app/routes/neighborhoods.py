from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.neighborhood import Neighborhood
from app.schemas.neighborhood import NeighborhoodResponse

router = APIRouter(prefix="/neighborhoods", tags=["Neighborhoods"])


@router.get("", response_model=list[NeighborhoodResponse])
def list_neighborhoods(db: Session = Depends(get_db)) -> list[Neighborhood]:
    try:
        return list(db.scalars(select(Neighborhood)).all())
    except SQLAlchemyError:
        return []


@router.get("/{neighborhood_id}", response_model=NeighborhoodResponse)
def get_neighborhood(neighborhood_id: int, db: Session = Depends(get_db)) -> Neighborhood:
    neighborhood = db.get(Neighborhood, neighborhood_id)
    if not neighborhood:
        raise HTTPException(status_code=404, detail="Neighborhood not found.")
    return neighborhood
