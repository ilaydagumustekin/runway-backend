from datetime import datetime

from pydantic import BaseModel, Field


class RouteHistoryCreate(BaseModel):
    route_name: str = Field(min_length=1, max_length=255)
    start_latitude: float
    start_longitude: float
    destination_latitude: float
    destination_longitude: float
    estimated_duration_minutes: int = Field(gt=0)
    environmental_score: float = Field(ge=0)


class RouteHistoryResponse(BaseModel):
    id: int
    user_id: int
    route_name: str
    start_latitude: float
    start_longitude: float
    destination_latitude: float
    destination_longitude: float
    estimated_duration_minutes: int
    environmental_score: float
    created_at: datetime

    model_config = {"from_attributes": True}
