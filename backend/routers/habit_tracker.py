"""习惯打卡路由（含日历数据）"""
from typing import Optional, List
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_
from pydantic import BaseModel
from database import get_db, User, Habit, HabitCheckin
from routers.auth import get_current_user

router = APIRouter()

class HabitCheckinRequest(BaseModel):
    habit_id: int
    check_date: Optional[date] = None

class HabitWithCheckins(BaseModel):
    id: int
    name: str
    frequency: str
    target: int
    current_streak: int
    created_at: datetime
    checkin_dates: List[str]

class MonthCheckins(BaseModel):
    habit_id: int
    habit_name: str
    dates: List[str]

@router.get("/habits", response_model=List[HabitWithCheckins])
def get_habits_with_checkins(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    habits = db.query(Habit).filter(Habit.user_id == current_user.id).all()
    result = []
    for h in habits:
        checkins = db.query(HabitCheckin).filter(
            HabitCheckin.habit_id == h.id,
            HabitCheckin.user_id == current_user.id,
        ).all()
        result.append(HabitWithCheckins(
            id=h.id,
            name=h.name,
            frequency=h.frequency,
            target=h.target,
            current_streak=h.current_streak,
            created_at=h.created_at,
            checkin_dates=[c.date.isoformat() for c in checkins],
        ))
    return result

@router.post("/habits", response_model=HabitWithCheckins)
def create_habit(
    name: str,
    frequency: str = "daily",
    target: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    h = Habit(user_id=current_user.id, name=name, frequency=frequency, target=target)
    db.add(h)
    db.commit()
    db.refresh(h)
    return HabitWithCheckins(
        id=h.id, name=h.name, frequency=h.frequency, target=h.target,
        current_streak=h.current_streak, created_at=h.created_at, checkin_dates=[],
    )

@router.post("/checkin")
def checkin_habit(
    req: HabitCheckinRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_date = req.check_date or date.today()
    existing = db.query(HabitCheckin).filter(
        HabitCheckin.habit_id == req.habit_id,
        HabitCheckin.user_id == current_user.id,
        HabitCheckin.date == check_date,
    ).first()
    if existing:
        return {"streak": _calc_streak(db, current_user.id, req.habit_id), "already_checked": True}

    checkin = HabitCheckin(
        user_id=current_user.id,
        habit_id=req.habit_id,
        date=check_date,
    )
    db.add(checkin)
    _update_streak(db, current_user.id, req.habit_id)
    db.commit()
    return {"streak": _calc_streak(db, current_user.id, req.habit_id), "already_checked": False}

def _calc_streak(db, user_id, habit_id):
    habit = db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == user_id).first()
    return habit.current_streak if habit else 0

def _update_streak(db, user_id, habit_id):
    habit = db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == user_id).first()
    if not habit:
        return
    checkins = db.query(HabitCheckin).filter(
        HabitCheckin.habit_id == habit_id,
        HabitCheckin.user_id == user_id,
    ).order_by(HabitCheckin.date.desc()).all()
    if not checkins:
        habit.current_streak = 0
        return
    streak = 0
    d = date.today()
    for c in checkins:
        if c.date == d:
            streak += 1
            d -= timedelta(days=1)
        elif c.date == d + timedelta(days=1):
            streak += 1
            d = c.date - timedelta(days=1)
        else:
            break
    habit.current_streak = streak

@router.delete("/habits/{habit_id}")
def delete_habit(
    habit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.query(HabitCheckin).filter(
        HabitCheckin.habit_id == habit_id,
        HabitCheckin.user_id == current_user.id,
    ).delete(synchronize_session=False)
    db.query(Habit).filter(
        Habit.id == habit_id,
        Habit.user_id == current_user.id,
    ).delete(synchronize_session=False)
    db.commit()
    return {"ok": True}

@router.delete("/checkin")
def delete_checkin(
    habit_id: int,
    check_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.query(HabitCheckin).filter(
        HabitCheckin.habit_id == habit_id,
        HabitCheckin.user_id == current_user.id,
        HabitCheckin.date == check_date,
    ).delete(synchronize_session=False)
    _update_streak(db, current_user.id, habit_id)
    db.commit()
    return {"ok": True}

@router.get("/calendar/{year}/{month}", response_model=List[MonthCheckins])
def get_calendar_checkins(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)

    habits = db.query(Habit).filter(Habit.user_id == current_user.id).all()
    result = []
    for h in habits:
        checkins = db.query(HabitCheckin).filter(
            HabitCheckin.habit_id == h.id,
            HabitCheckin.user_id == current_user.id,
            HabitCheckin.date >= start,
            HabitCheckin.date < end,
        ).all()
        result.append(MonthCheckins(
            habit_id=h.id,
            habit_name=h.name,
            dates=[c.date.isoformat() for c in checkins],
        ))
    return result
