from pydantic import BaseModel


class Coordinate(BaseModel):
    latitude: float
    longitude: float


class RouteRecommendRequest(BaseModel):
    start: Coordinate
    destination: Coordinate


class RouteRecommendResponse(BaseModel):
    route_name: str
    estimated_duration_minutes: int
    environmental_score: float
    path: list[Coordinate]
