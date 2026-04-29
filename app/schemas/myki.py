from pydantic import BaseModel


class MYKIResponse(BaseModel):
    neighborhood_id: int
    score: float
    category: str
