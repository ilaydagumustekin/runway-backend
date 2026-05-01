from pydantic import BaseModel, Field


class NeighborhoodUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    city: str | None = Field(default=None, min_length=1, max_length=80)
    district: str | None = Field(default=None, min_length=1, max_length=80)
    latitude: float | None = None
    longitude: float | None = None
    boundary_data: str | None = None


class EnvironmentalDataUpdate(BaseModel):
    pm25: float | None = Field(default=None, ge=0)
    pm10: float | None = Field(default=None, ge=0)
    no2: float | None = Field(default=None, ge=0)
    o3: float | None = Field(default=None, ge=0)
    aqi: float | None = Field(default=None, ge=0)
    green_area_ratio: float | None = Field(default=None, ge=0, le=100)
    noise_level_dba: float | None = Field(default=None, ge=0)


class AirQualityUpdate(BaseModel):
    pm25: float | None = Field(default=None, ge=0)
    pm10: float | None = Field(default=None, ge=0)
    no2: float | None = Field(default=None, ge=0)
    o3: float | None = Field(default=None, ge=0)
    aqi: float | None = Field(default=None, ge=0)


class NoiseUpdate(BaseModel):
    noise_level_dba: float = Field(ge=0)


class GreenAreaUpdate(BaseModel):
    green_area_ratio: float = Field(ge=0, le=100)


class RouteHistoryUpdate(BaseModel):
    route_name: str | None = Field(default=None, min_length=1, max_length=255)
    start_latitude: float | None = None
    start_longitude: float | None = None
    destination_latitude: float | None = None
    destination_longitude: float | None = None
    estimated_duration_minutes: int | None = Field(default=None, gt=0)
    environmental_score: float | None = Field(default=None, ge=0)
