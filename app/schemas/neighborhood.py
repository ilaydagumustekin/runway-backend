from pydantic import BaseModel


class NeighborhoodResponse(BaseModel):
    id: int
    name: str
    city: str
    district: str
    latitude: float
    longitude: float
    boundary_data: str | None = None

    model_config = {"from_attributes": True}
