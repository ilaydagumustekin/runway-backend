from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.myki import MYKIResponse
from app.services.myki_service import get_myki_for_neighborhood

router = APIRouter(prefix="/myki", tags=["MYKI"])


@router.get("/{neighborhood_id}", response_model=MYKIResponse)
def get_myki(neighborhood_id: int, db: Session = Depends(get_db)) -> MYKIResponse:
    result = get_myki_for_neighborhood(db, neighborhood_id)
    if result is None:
        raise HTTPException(
            status_code=404, detail="No environmental data found for this neighborhood."
        )
    return result
