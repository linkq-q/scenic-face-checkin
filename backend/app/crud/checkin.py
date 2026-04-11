from datetime import date, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.checkin import CheckinLog
from app.models.ticket import Ticket


def create_log(
    db: Session,
    ticket_id: int,
    visitor_id: int,
    gate_id: str | None,
    match_score: float | None,
) -> CheckinLog:
    log = CheckinLog(
        ticket_id=ticket_id,
        visitor_id=visitor_id,
        gate_id=gate_id,
        match_score=match_score,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_unused_ticket(
    db: Session,
    visitor_id: int,
    visit_date: date,
) -> Ticket | None:
    """查找游客在指定日期的未使用门票。"""
    return (
        db.query(Ticket)
        .filter(
            Ticket.visitor_id == visitor_id,
            Ticket.visit_date == visit_date,
            Ticket.status == "unused",
        )
        .first()
    )


def has_used_ticket(
    db: Session,
    visitor_id: int,
    visit_date: date,
) -> bool:
    """检查游客在指定日期是否已有 used 状态的门票（已核销过）。"""
    return (
        db.query(Ticket)
        .filter(
            Ticket.visitor_id == visitor_id,
            Ticket.visit_date == visit_date,
            Ticket.status == "used",
        )
        .count()
        > 0
    )


def get_daily_stats(db: Session, stat_date: date) -> dict:
    """
    返回指定日期的核销统计：
    { date, total_checkins, by_hour: [{hour, count}, ...] }
    """
    rows = (
        db.query(
            func.hour(CheckinLog.checked_at).label("hour"),
            func.count(CheckinLog.id).label("count"),
        )
        .filter(func.date(CheckinLog.checked_at) == stat_date)
        .group_by(func.hour(CheckinLog.checked_at))
        .order_by(func.hour(CheckinLog.checked_at))
        .all()
    )

    by_hour = [{"hour": row.hour, "count": row.count} for row in rows]
    total = sum(r["count"] for r in by_hour)

    return {
        "date": stat_date.isoformat(),
        "total_checkins": total,
        "by_hour": by_hour,
    }


def get_range_stats(db: Session, start: date, end: date) -> dict:
    """
    返回日期区间内每日核销数量：
    { records: [{date, count}, ...] }
    """
    rows = (
        db.query(
            func.date(CheckinLog.checked_at).label("dt"),
            func.count(CheckinLog.id).label("count"),
        )
        .filter(
            func.date(CheckinLog.checked_at) >= start,
            func.date(CheckinLog.checked_at) <= end,
        )
        .group_by(func.date(CheckinLog.checked_at))
        .order_by(func.date(CheckinLog.checked_at))
        .all()
    )

    records = [
        {"date": str(row.dt), "count": row.count}
        for row in rows
    ]
    return {"records": records}


def get_realtime_stats(db: Session) -> dict:
    """
    返回实时概况：
    { today_total, last_hour_count, last_checkin_at }
    """
    today = date.today()
    one_hour_ago = datetime.now() - timedelta(hours=1)

    today_total: int = (
        db.query(func.count(CheckinLog.id))
        .filter(func.date(CheckinLog.checked_at) == today)
        .scalar()
        or 0
    )

    last_hour_count: int = (
        db.query(func.count(CheckinLog.id))
        .filter(CheckinLog.checked_at >= one_hour_ago)
        .scalar()
        or 0
    )

    last_checkin_at = (
        db.query(func.max(CheckinLog.checked_at))
        .scalar()
    )

    return {
        "today_total": today_total,
        "last_hour_count": last_hour_count,
        "last_checkin_at": last_checkin_at,
    }
