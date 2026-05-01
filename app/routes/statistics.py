from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.data_sources import DataSourceResponse
from app.schemas.statistics import (
    NeighborhoodChartDataResponse,
    NeighborhoodHistoryItem,
    NeighborhoodSummaryResponse,
)
from app.services.statistics_service import (
    build_neighborhood_chart_data,
    build_neighborhood_summary,
    get_data_source_by_slug,
    get_latest_environmental_record,
    get_neighborhood_history,
    get_neighborhood_or_none,
    list_data_sources,
)

statistics_router = APIRouter(prefix="/statistics", tags=["Statistics"])
data_sources_router = APIRouter(prefix="/data-sources", tags=["Data Sources"])


@statistics_router.get("/neighborhood/{neighborhood_id}/summary", response_model=NeighborhoodSummaryResponse)
def get_neighborhood_summary(neighborhood_id: int, db: Session = Depends(get_db)) -> NeighborhoodSummaryResponse:
    neighborhood = get_neighborhood_or_none(db, neighborhood_id)
    if not neighborhood:
        raise HTTPException(status_code=404, detail="Neighborhood not found.")

    latest_record = get_latest_environmental_record(db, neighborhood_id)
    if not latest_record:
        raise HTTPException(status_code=404, detail="No environmental data found for this neighborhood.")

    summary = build_neighborhood_summary(db, neighborhood_id)
    if not summary:
        raise HTTPException(status_code=404, detail="No environmental data found for this neighborhood.")
    return summary


@statistics_router.get("/neighborhood/{neighborhood_id}/history", response_model=list[NeighborhoodHistoryItem])
def get_neighborhood_statistics_history(
    neighborhood_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[NeighborhoodHistoryItem]:
    neighborhood = get_neighborhood_or_none(db, neighborhood_id)
    if not neighborhood:
        raise HTTPException(status_code=404, detail="Neighborhood not found.")
    return get_neighborhood_history(db, neighborhood_id, limit)


@statistics_router.get(
    "/neighborhood/{neighborhood_id}/chart-data", response_model=NeighborhoodChartDataResponse
)
def get_neighborhood_chart_data(
    neighborhood_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> NeighborhoodChartDataResponse:
    neighborhood = get_neighborhood_or_none(db, neighborhood_id)
    if not neighborhood:
        raise HTTPException(status_code=404, detail="Neighborhood not found.")
    return build_neighborhood_chart_data(db, neighborhood_id, limit)


@data_sources_router.get("", response_model=list[DataSourceResponse])
def get_all_data_sources() -> list[DataSourceResponse]:
    return list_data_sources()


@data_sources_router.get("/{source_name}", response_model=DataSourceResponse)
def get_data_source_detail(source_name: str) -> DataSourceResponse:
    source = get_data_source_by_slug(source_name)
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found.")
    return source
