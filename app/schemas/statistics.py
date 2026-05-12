from datetime import datetime

from pydantic import BaseModel


class NeighborhoodSummaryResponse(BaseModel):
    neighborhood_id: int
    neighborhood_name: str
    city: str
    district: str
    latest_aqi: float | None
    latest_pm25: float | None
    latest_pm10: float | None
    latest_noise_level_dba: float | None
    latest_green_area_ratio: float | None
    myki_score: float | None
    myki_category: str | None
    updated_at: datetime


class NeighborhoodHistoryItem(BaseModel):
    created_at: datetime
    aqi: float | None
    pm25: float | None
    pm10: float | None
    noise_level_dba: float | None
    green_area_ratio: float | None


class NeighborhoodChartDataResponse(BaseModel):
    neighborhood_id: int
    labels: list[str]
    aqi: list[float | None]
    noise_level_dba: list[float | None]
    green_area_ratio: list[float | None]
    myki_score: list[float | None]
