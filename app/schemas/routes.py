from pydantic import BaseModel


class Coordinate(BaseModel):
    latitude: float
    longitude: float


class RouteRecommendRequest(BaseModel):
    start: Coordinate
    destination: Coordinate
    transport_mode: str = "walking"  # walking | bicycle | scooter


class RouteRecommendResponse(BaseModel):
    route_name: str
    estimated_duration_minutes: int
    environmental_score: float | None
    path: list[Coordinate]
    distance_km: float = 0.0
    transport_mode: str = "walking"
    speed_kmh: float = 5.0
    snap_to_roads: bool = False
    waypoints: list[Coordinate] = []
    routing_source: str = "centroid"  # "openrouteservice" | "centroid"
