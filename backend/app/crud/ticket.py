from datetime import date

from sqlalchemy.orm import Session

from app.models.ticket import Ticket
from app.models.visitor import Visitor


def create(
    db: Session,
    visitor_id: int,
    scenic_name: str,
    visit_date: date,
) -> Ticket:
    ticket = Ticket(
        visitor_id=visitor_id,
        scenic_name=scenic_name,
        visit_date=visit_date,
        status="unused",
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def get_by_id(db: Session, ticket_id: int) -> Ticket | None:
    return db.get(Ticket, ticket_id)


def get_detail(db: Session, ticket_id: int) -> dict | None:
    """返回门票详情，附带游客姓名。"""
    row = (
        db.query(Ticket, Visitor.name)
        .join(Visitor, Ticket.visitor_id == Visitor.id)
        .filter(Ticket.id == ticket_id)
        .first()
    )
    if row is None:
        return None
    ticket, visitor_name = row
    return {
        "id": ticket.id,
        "visitor_id": ticket.visitor_id,
        "visitor_name": visitor_name,
        "scenic_name": ticket.scenic_name,
        "visit_date": ticket.visit_date,
        "status": ticket.status,
        "created_at": ticket.created_at,
    }


def list_tickets(
    db: Session,
    visitor_id: int | None = None,
    visit_date: date | None = None,
    status: str | None = None,
) -> list[Ticket]:
    query = db.query(Ticket)
    if visitor_id is not None:
        query = query.filter(Ticket.visitor_id == visitor_id)
    if visit_date is not None:
        query = query.filter(Ticket.visit_date == visit_date)
    if status is not None:
        query = query.filter(Ticket.status == status)
    return query.order_by(Ticket.id.desc()).all()


def update_status(db: Session, ticket: Ticket, status: str) -> Ticket:
    ticket.status = status
    db.commit()
    db.refresh(ticket)
    return ticket
