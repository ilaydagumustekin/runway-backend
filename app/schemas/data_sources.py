from pydantic import BaseModel


class DataSourceResponse(BaseModel):
    slug: str
    name: str
    type: str
    description: str
    status: str
    usage_area: str
