"""健康路由"""
from typing import Optional, List
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db, User, HealthRecord
from routers.auth import get_current_user

router = APIRouter()

class HealthRecordCreate(BaseModel):
    date: Optional[date] = None
    weight: Optional[float] = None
    steps: Optional[int] = 0
    sleep_hours: Optional[float] = None
    mood: Optional[str] = None
    notes: Optional[str] = None

class HealthRecordOut(BaseModel):
    id: int
    date: date
    weight: Optional[float]
    steps: int
    sleep_hours: Optional[float]
    mood: Optional[str]
    notes: Optional[str]
    class Config:
        from_attributes = True

class HealthStats(BaseModel):
    total_records: int
    avg_weight: Optional[float]
    avg_sleep: Optional[float]
    avg_steps: Optional[float]
    current_streak: int

@router.get("/records", response_model=List[HealthRecordOut])
def get_records(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(HealthRecord).filter(HealthRecord.user_id == current_user.id)
    if start_date:
        q = q.filter(HealthRecord.date >= start_date)
    if end_date:
        q = q.filter(HealthRecord.date <= end_date)
    return q.order_by(HealthRecord.date.desc()).limit(limit).all()

@router.post("/records", response_model=HealthRecordOut)
def create_record(
    record: HealthRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rec = HealthRecord(
        user_id=current_user.id,
        date=record.date or date.today(),
        weight=record.weight,
        steps=record.steps or 0,
        sleep_hours=record.sleep_hours,
        mood=record.mood,
        notes=record.notes,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec

@router.get("/stats", response_model=HealthStats)
def get_stats(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from datetime import timedelta
    start = date.today() - timedelta(days=days)
    records = db.query(HealthRecord).filter(
        HealthRecord.user_id == current_user.id,
        HealthRecord.date >= start,
    ).all()
    if not records:
        return HealthStats(total_records=0, avg_weight=None, avg_sleep=None, avg_steps=None, current_streak=0)
    weights = [r.weight for r in records if r.weight]
    sleeps = [r.sleep_hours for r in records if r.sleep_hours]
    steps = [r.steps for r in records if r.steps]
    streak = len(records)
    return HealthStats(
        total_records=len(records),
        avg_weight=round(sum(weights)/len(weights), 1) if weights else None,
        avg_sleep=round(sum(sleeps)/len(sleeps), 1) if sleeps else None,
        avg_steps=int(sum(steps)/len(steps)) if steps else 0,
        current_streak=streak,
    )
