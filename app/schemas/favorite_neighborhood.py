from datetime import datetime

from pydantic import BaseModel


class FavoriteNeighborhoodItem(BaseModel):
    id: int
    name: str
    city: str
    district: str
    latitude: float
    longitude: float

    model_config = {"from_attributes": True}


class FavoriteNeighborhoodResponse(BaseModel):
    id: int
    user_id: int
    neighborhood_id: int
    created_at: datetime
    neighborhood: FavoriteNeighborhoodItem

    model_config = {"from_attributes": True}


class FavoriteNeighborhoodListResponse(BaseModel):
    favorites: list[FavoriteNeighborhoodResponse]
