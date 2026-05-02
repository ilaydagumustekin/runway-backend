from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.location import (
    NearbyNeighborhoodResponse,
    NeighborhoodMarkerResponse,
    NeighborhoodMarkerWithScoreResponse,
    NearestNeighborhoodResponse,
)
from app.services.location_service import (
    find_nearest_neighborhood,
    find_nearby_neighborhoods,
    get_neighborhood_markers,
    get_neighborhood_markers_with_scores,
)

router = APIRouter(tags=["Location"])


@router.get("/location/nearest-neighborhood", response_model=NearestNeighborhoodResponse)
def get_nearest_neighborhood(
    latitude: float = Query(...),
    longitude: float = Query(...),
    db: Session = Depends(get_db),
) -> NearestNeighborhoodResponse:
    result = find_nearest_neighborhood(db, latitude, longitude)
    if not result:
        raise HTTPException(status_code=404, detail="No neighborhoods found.")
    return result


@router.get("/location/nearby-neighborhoods", response_model=list[NearbyNeighborhoodResponse])
def get_nearby_neighborhoods(
    latitude: float = Query(...),
    longitude: float = Query(...),
    radius_km: float = Query(default=5.0, gt=0),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[NearbyNeighborhoodResponse]:
    return find_nearby_neighborhoods(db, latitude, longitude, radius_km, limit)


@router.get("/map/neighborhood-markers", response_model=list[NeighborhoodMarkerResponse])
def list_neighborhood_markers(db: Session = Depends(get_db)) -> list[NeighborhoodMarkerResponse]:
    return get_neighborhood_markers(db)


@router.get(
    "/map/neighborhood-markers/with-scores",
    response_model=list[NeighborhoodMarkerWithScoreResponse],
)
def list_neighborhood_markers_with_scores(
    db: Session = Depends(get_db),
) -> list[NeighborhoodMarkerWithScoreResponse]:
    return get_neighborhood_markers_with_scores(db)
