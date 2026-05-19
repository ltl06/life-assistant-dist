"""日记路由"""
from typing import Optional, List
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db, User, Diary
from routers.auth import get_current_user

router = APIRouter()

class DiaryCreate(BaseModel):
    title: Optional[str] = None
    content: str
    mood: Optional[str] = None
    tags: Optional[str] = None
    date: Optional[date] = None

class DiaryOut(BaseModel):
    id: int
    date: date
    title: Optional[str]
    content: str
    mood: Optional[str]
    tags: Optional[str]
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class DiaryStats(BaseModel):
    total_count: int
    streak_days: int
    moods: dict

@router.get("/records", response_model=List[DiaryOut])
def get_diaries(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Diary).filter(Diary.user_id == current_user.id)
    if start_date:
        q = q.filter(Diary.date >= start_date)
    if end_date:
        q = q.filter(Diary.date <= end_date)
    return q.order_by(Diary.date.desc()).limit(limit).all()

@router.get("/records/{diary_id}", response_model=DiaryOut)
def get_diary(
    diary_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    d = db.query(Diary).filter(Diary.id == diary_id, Diary.user_id == current_user.id).first()
    if not d:
        raise HTTPException(status_code=404, detail="日记不存在")
    return d

@router.post("/records", response_model=DiaryOut)
def create_diary(
    diary: DiaryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    d = Diary(
        user_id=current_user.id,
        title=diary.title,
        content=diary.content,
        mood=diary.mood,
        tags=diary.tags,
        date=diary.date or date.today(),
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    return d

@router.put("/records/{diary_id}", response_model=DiaryOut)
def update_diary(
    diary_id: int,
    diary: DiaryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    d = db.query(Diary).filter(Diary.id == diary_id, Diary.user_id == current_user.id).first()
    if not d:
        raise HTTPException(status_code=404, detail="日记不存在")
    if diary.title is not None:
        d.title = diary.title
    d.content = diary.content
    if diary.mood is not None:
        d.mood = diary.mood
    if diary.tags is not None:
        d.tags = diary.tags
    from datetime import datetime
    d.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(d)
    return d

@router.delete("/records/{diary_id}")
def delete_diary(
    diary_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    d = db.query(Diary).filter(Diary.id == diary_id, Diary.user_id == current_user.id).first()
    if d:
        db.delete(d)
        db.commit()
    return {"ok": True}

@router.get("/stats", response_model=DiaryStats)
def get_diary_stats(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from datetime import timedelta
    start = date.today() - timedelta(days=days)
    records = db.query(Diary).filter(
        Diary.user_id == current_user.id,
        Diary.date >= start,
    ).all()

    mood_count = {}
    for r in records:
        m = r.mood or "未记录"
        mood_count[m] = mood_count.get(m, 0) + 1

    streak = 0
    d = date.today()
    for _ in range(365):
        found = any(x.date == d for x in records)
        if found:
            streak += 1
            d -= timedelta(days=1)
        elif streak > 0:
            break
        else:
            d -= timedelta(days=1)

    return DiaryStats(total_count=len(records), streak_days=streak, moods=mood_count)
