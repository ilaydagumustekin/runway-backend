from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class NavigationStartRequest(BaseModel):
    route_history_id: int | None = None
    route_name: str | None = Field(default=None, min_length=1, max_length=255)
    start_latitude: float | None = None
    start_longitude: float | None = None
    destination_latitude: float | None = None
    destination_longitude: float | None = None

    @model_validator(mode="after")
    def validate_input_mode(self) -> "NavigationStartRequest":
        if self.route_history_id is not None:
            return self

        required_fields = [
            self.route_name,
            self.start_latitude,
            self.start_longitude,
            self.destination_latitude,
            self.destination_longitude,
        ]
        if any(value is None for value in required_fields):
            raise ValueError(
                "Either route_history_id or direct route information must be provided."
            )
        return self


class NavigationSessionResponse(BaseModel):
    id: int
    user_id: int
    route_history_id: int | None
    route_name: str
    start_latitude: float
    start_longitude: float
    destination_latitude: float
    destination_longitude: float
    status: str
    started_at: datetime
    ended_at: datetime | None

    model_config = {"from_attributes": True}


class NavigationStatusUpdate(BaseModel):
    status: str
