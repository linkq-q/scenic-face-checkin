from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.crud import checkin as checkin_crud
from app.database import get_db

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/daily")
def daily_stats(
    date: date = Query(..., description="统计日期，格式 YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """按小时返回指定日期的核销量。"""
    return checkin_crud.get_daily_stats(db, date)


@router.get("/range")
def range_stats(
    start: date = Query(..., description="开始日期 YYYY-MM-DD"),
    end: date = Query(..., description="结束日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """按日汇总指定区间内每天的核销量。"""
    if end < start:
        raise HTTPException(status_code=400, detail="end 不能早于 start")
    return checkin_crud.get_range_stats(db, start, end)


@router.get("/realtime")
def realtime_stats(db: Session = Depends(get_db)):
    """返回今日核销总数、最近一小时数量、最后核销时间。"""
    return checkin_crud.get_realtime_stats(db)
