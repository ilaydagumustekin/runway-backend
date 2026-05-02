from datetime import datetime

from pydantic import BaseModel

from app.schemas.data_sources import DataSourceResponse
from app.schemas.neighborhood import NeighborhoodResponse


class NeighborhoodDetailEnvironmentalData(BaseModel):
    id: int
    aqi: float
    pm25: float
    pm10: float
    no2: float
    o3: float
    green_area_ratio: float
    noise_level_dba: float
    created_at: datetime

    model_config = {"from_attributes": True}


class NeighborhoodDetailMYKI(BaseModel):
    score: float
    category: str


class NeighborhoodDetailChartSummary(BaseModel):
    labels: list[str]
    aqi: list[float]
    noise_level_dba: list[float]
    green_area_ratio: list[float]
    myki_score: list[float]


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
