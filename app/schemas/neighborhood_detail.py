from datetime import datetime

from pydantic import BaseModel

from app.schemas.data_sources import DataSourceResponse
from app.schemas.neighborhood import NeighborhoodResponse


class NeighborhoodDetailEnvironmentalData(BaseModel):
    id: int
    aqi: float | None
    pm25: float | None
    pm10: float | None
    no2: float | None
    o3: float | None
    green_area_ratio: float | None
    noise_level_dba: float | None
    created_at: datetime

    model_config = {"from_attributes": True}


class NeighborhoodDetailMYKI(BaseModel):
    score: float
    category: str


class NeighborhoodDetailChartSummary(BaseModel):
    labels: list[str]
    aqi: list[float | None]
    noise_level_dba: list[float | None]
    green_area_ratio: list[float | None]
    myki_score: list[float | None]


class NeighborhoodDetailDataSource(BaseModel):
    name: str
    type: str
    status: str


class NeighborhoodDetailResponse(BaseModel):
    neighborhood: NeighborhoodResponse
    latest_environmental_data: NeighborhoodDetailEnvironmentalData | None
    myki: NeighborhoodDetailMYKI | None
    chart_summary: NeighborhoodDetailChartSummary
    data_sources: list[NeighborhoodDetailDataSource]
