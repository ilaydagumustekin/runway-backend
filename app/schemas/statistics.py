from datetime import datetime

from pydantic import BaseModel


class NeighborhoodSummaryResponse(BaseModel):
    neighborhood_id: int
    neighborhood_name: str
    city: str
    district: str
    latest_aqi: float
    latest_pm25: float
    latest_pm10: float
    latest_noise_level_dba: float
    latest_green_area_ratio: float
    myki_score: float
    myki_category: str
    updated_at: datetime


class NeighborhoodHistoryItem(BaseModel):
    created_at: datetime
    aqi: float
    pm25: float
    pm10: float
    noise_level_dba: float
    green_area_ratio: float


class NeighborhoodChartDataResponse(BaseModel):
    neighborhood_id: int
    labels: list[str]
    aqi: list[float]
    noise_level_dba: list[float]
    green_area_ratio: list[float]
    myki_score: list[float]
