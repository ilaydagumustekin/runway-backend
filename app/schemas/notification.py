from datetime import datetime

from pydantic import BaseModel, Field


class NotificationCreate(BaseModel):
    user_id: int | None = None
    neighborhood_id: int | None = None
    title: str = Field(min_length=1, max_length=255)
    message: str = Field(min_length=1)
    notification_type: str = Field(min_length=1, max_length=50)
    severity: str = Field(min_length=1, max_length=30)


class NotificationResponse(BaseModel):
    id: int
    user_id: int | None
    neighborhood_id: int | None
    title: str
    message: str
    notification_type: str
    severity: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationUpdate(BaseModel):
    is_read: bool
