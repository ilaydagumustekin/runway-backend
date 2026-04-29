from datetime import datetime

from pydantic import BaseModel, Field


class EnvironmentalDataCreate(BaseModel):
    neighborhood_id: int
    pm25: float = Field(ge=0)
    pm10: float = Field(ge=0)
    no2: float = Field(ge=0)
    o3: float = Field(ge=0)
    aqi: float = Field(ge=0)
    green_area_ratio: float = Field(ge=0, le=100)
    noise_level_dba: float = Field(ge=0)


class EnvironmentalDataResponse(EnvironmentalDataCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}
