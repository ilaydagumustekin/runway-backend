from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class NoiseMeasurementCreate(BaseModel):
    neighborhood_id: int
    noise_level_dba: float = Field(ge=0)
    latitude: float | None = None
    longitude: float | None = None

    @model_validator(mode="before")
    @classmethod
    def support_legacy_dba_alias(cls, data: object) -> object:
        if isinstance(data, dict) and "noise_level_dba" not in data and "dba" in data:
            data = data.copy()
            data["noise_level_dba"] = data["dba"]
        return data


class NoiseMeasurementResponse(NoiseMeasurementCreate):
    id: int
    measured_at: datetime

    model_config = {"from_attributes": True}
