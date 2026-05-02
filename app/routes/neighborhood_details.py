from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.neighborhood_detail import NeighborhoodDetailResponse
from app.services.neighborhood_detail_service import build_neighborhood_detail_response

router = APIRouter(tags=["Neighborhood Details"])


@router.get("/neighborhoods/{neighborhood_id}/details", response_model=NeighborhoodDetailResponse)
def get_neighborhood_details(
    neighborhood_id: int, db: Session = Depends(get_db)
) -> NeighborhoodDetailResponse:
    detail = build_neighborhood_detail_response(db, neighborhood_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Neighborhood not found.")
    return detail
