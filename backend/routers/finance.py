"""财务路由"""
from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db, User, FinanceRecord
from routers.auth import get_current_user

router = APIRouter()

class FinanceCreate(BaseModel):
    type: str
    amount: float
    category: str
    description: Optional[str] = None
    date: Optional[date] = None

class FinanceOut(BaseModel):
    id: int
    type: str
    amount: float
    category: str
    description: Optional[str]
    date: date
    class Config:
        from_attributes = True

class FinanceStats(BaseModel):
    total_income: float
    total_expense: float
    balance: float
    top_expense_category: Optional[str]
    monthly_comparison: dict

@router.get("/records", response_model=List[FinanceOut])
def get_records(
    record_type: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(FinanceRecord).filter(FinanceRecord.user_id == current_user.id)
    if record_type:
        q = q.filter(FinanceRecord.type == record_type)
    if category:
        q = q.filter(FinanceRecord.category == category)
    if start_date:
        q = q.filter(FinanceRecord.date >= start_date)
    if end_date:
        q = q.filter(FinanceRecord.date <= end_date)
    return q.order_by(FinanceRecord.date.desc()).limit(limit).all()

@router.post("/records", response_model=FinanceOut)
def create_record(
    record: FinanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rec = FinanceRecord(
        user_id=current_user.id,
        type=record.type,
        amount=record.amount,
        category=record.category,
        description=record.description,
        date=record.date or date.today(),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec

@router.get("/stats", response_model=FinanceStats)
def get_stats(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from datetime import timedelta
    start = date.today() - timedelta(days=days)
    records = db.query(FinanceRecord).filter(
        FinanceRecord.user_id == current_user.id,
        FinanceRecord.date >= start,
    ).all()
    income = sum(r.amount for r in records if r.type == "income")
    expense = sum(r.amount for r in records if r.type == "expense")
    expense_by_cat = {}
    for r in records:
        if r.type == "expense":
            expense_by_cat[r.category] = expense_by_cat.get(r.category, 0) + r.amount
    top_cat = max(expense_by_cat, key=expense_by_cat.get) if expense_by_cat else None
    return FinanceStats(
        total_income=round(income, 2),
        total_expense=round(expense, 2),
        balance=round(income - expense, 2),
        top_expense_category=top_cat,
        monthly_comparison={},
    )

CATEGORIES = {
    "income": ["工资", "奖金", "投资收益", "兼职", "其他收入"],
    "expense": ["餐饮", "交通", "购物", "居住", "医疗", "教育", "娱乐", "通讯", "服装", "其他"],
}
