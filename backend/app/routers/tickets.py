from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas.ticket import TicketCreate, TicketDetail, TicketResponse

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


@router.post("", response_model=TicketResponse, status_code=201)
def create_ticket(body: TicketCreate, db: Session = Depends(get_db)):
    if crud.visitor.get_by_id(db, body.visitor_id) is None:
        raise HTTPException(status_code=404, detail="游客不存在")

    ticket = crud.ticket.create(
        db,
        visitor_id=body.visitor_id,
        scenic_name=body.scenic_name,
        visit_date=body.visit_date,
    )
    return TicketResponse(
        ticket_id=ticket.id,
        visitor_id=ticket.visitor_id,
        scenic_name=ticket.scenic_name,
        visit_date=ticket.visit_date,
        status=ticket.status,
    )


@router.get("", response_model=list[TicketResponse])
def list_tickets(
    visitor_id: int | None = None,
    date: date | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    tickets = crud.ticket.list_tickets(
        db,
        visitor_id=visitor_id,
        visit_date=date,
        status=status,
    )
    return [
        TicketResponse(
            ticket_id=t.id,
            visitor_id=t.visitor_id,
            scenic_name=t.scenic_name,
            visit_date=t.visit_date,
            status=t.status,
        )
        for t in tickets
    ]


@router.get("/{ticket_id}", response_model=TicketDetail)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    detail = crud.ticket.get_detail(db, ticket_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="门票不存在")
    return TicketDetail(**detail)
