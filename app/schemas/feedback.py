from datetime import datetime

from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    subject: str = Field(min_length=1, max_length=255)
    message: str = Field(min_length=1)
    rating: int | None = Field(default=None, ge=1, le=5)
    category: str = Field(min_length=1, max_length=50)


class FeedbackResponse(BaseModel):
    id: int
    user_id: int
    subject: str
    message: str
    rating: int | None
    category: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FeedbackStatusUpdate(BaseModel):
    status: str = Field(min_length=1, max_length=30)
