from pydantic import BaseModel


class NearestNeighborhoodItem(BaseModel):
    id: int
    name: str
    city: str
    district: str
    latitude: float
    longitude: float


class NearestNeighborhoodResponse(BaseModel):
    neighborhood: NearestNeighborhoodItem
    distance_km: float


class NearbyNeighborhoodResponse(BaseModel):
    id: int
    name: str
    city: str
    district: str
    latitude: float
    longitude: float
    distance_km: float


class NeighborhoodMarkerResponse(BaseModel):
    id: int
    name: str
    city: str
    district: str
    latitude: float
    longitude: float


class NeighborhoodMarkerWithScoreResponse(BaseModel):
    id: int
    name: str
    city: str
    district: str
    latitude: float
    longitude: float
    myki_score: float | None
    myki_category: str | None
