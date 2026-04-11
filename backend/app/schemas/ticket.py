from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel


TicketStatus = Literal["unused", "used", "expired"]


class TicketCreate(BaseModel):
    visitor_id: int
    scenic_name: str
    visit_date: date


class TicketResponse(BaseModel):
    ticket_id: int
    visitor_id: int
    scenic_name: str
    visit_date: date
    status: TicketStatus

    model_config = {"from_attributes": True}


class TicketDetail(BaseModel):
    id: int
    visitor_id: int
    visitor_name: str
    scenic_name: str
    visit_date: date
    status: TicketStatus
    created_at: datetime
