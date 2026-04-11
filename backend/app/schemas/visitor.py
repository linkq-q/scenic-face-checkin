from datetime import datetime

from pydantic import BaseModel


class VisitorRegisterResponse(BaseModel):
    visitor_id: int
    name: str
    message: str


class VisitorDetail(BaseModel):
    id: int
    name: str
    phone: str
    avatar_url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
