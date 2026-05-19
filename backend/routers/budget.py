"""预算路由"""
from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from database import get_db, User, Budget, FinanceRecord
from routers.auth import get_current_user

router = APIRouter()

EXPENSE_CATEGORIES = ["餐饮", "交通", "购物", "居住", "医疗", "教育", "娱乐", "通讯", "服装", "其他"]

class BudgetCreate(BaseModel):
    year_month: str
    category: str
    budget_amount: float

class BudgetOut(BaseModel):
    id: int
    year_month: str
    category: str
    budget_amount: float
    class Config:
        from_attributes = True

class BudgetStatus(BaseModel):
    category: str
    budget: float
    spent: float
    remaining: float
    percent: float
    is_over: bool

class BudgetSummary(BaseModel):
    year_month: str
    total_budget: float
    total_spent: float
    overall_remaining: float
    overall_percent: float
    is_over: bool
    categories: List[BudgetStatus]

@router.get("/budgets", response_model=List[BudgetOut])
def get_budgets(
    year_month: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Budget).filter(Budget.user_id == current_user.id)
    if year_month:
        q = q.filter(Budget.year_month == year_month)
    return q.all()

@router.post("/budgets", response_model=BudgetOut)
def create_budget(
    budget: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(Budget).filter(
        Budget.user_id == current_user.id,
        Budget.year_month == budget.year_month,
        Budget.category == budget.category,
    ).first()
    if existing:
        existing.budget_amount = budget.budget_amount
        db.commit()
        db.refresh(existing)
        return existing
    b = Budget(
        user_id=current_user.id,
        year_month=budget.year_month,
        category=budget.category,
        budget_amount=budget.budget_amount,
    )
    db.add(b)
    db.commit()
    db.refresh(b)
    return b

@router.delete("/budgets/{budget_id}")
def delete_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    b = db.query(Budget).filter(Budget.id == budget_id, Budget.user_id == current_user.id).first()
    if b:
        db.delete(b)
        db.commit()
    return {"ok": True}

@router.get("/summary/{year_month}", response_model=BudgetSummary)
def get_budget_summary(
    year_month: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    budgets = db.query(Budget).filter(
        Budget.user_id == current_user.id,
        Budget.year_month == year_month,
    ).all()

    if not budgets:
        today = date.today()
        year_month = f"{today.year}-{today.month:02d}"
        budgets = db.query(Budget).filter(
            Budget.user_id == current_user.id,
            Budget.year_month == year_month,
        ).all()

    if not budgets:
        return BudgetSummary(
            year_month=year_month,
            total_budget=0, total_spent=0,
            overall_remaining=0, overall_percent=0,
            is_over=False, categories=[],
        )

    y, m = map(int, year_month.split("-"))
    start = date(y, m, 1)
    if m == 12:
        end = date(y + 1, 1, 1)
    else:
        end = date(y, m + 1, 1)

    spent_q = db.query(
        FinanceRecord.category,
        func.sum(FinanceRecord.amount).label("total"),
    ).filter(
        FinanceRecord.user_id == current_user.id,
        FinanceRecord.type == "expense",
        FinanceRecord.date >= start,
        FinanceRecord.date < end,
    ).group_by(FinanceRecord.category).all()

    spent_map = {r.category: float(r.total) for r in spent_q}
    total_spent = sum(spent_map.values())

    categories = []
    for b in budgets:
        spent = spent_map.get(b.category, 0.0)
        remaining = b.budget_amount - spent
        percent = round(spent / b.budget_amount * 100, 1) if b.budget_amount > 0 else 0
        categories.append(BudgetStatus(
            category=b.category,
            budget=b.budget_amount,
            spent=spent,
            remaining=remaining,
            percent=percent,
            is_over=spent > b.budget_amount,
        ))

    total_budget = sum(b.budget_amount for b in budgets)
    overall_remaining = total_budget - total_spent
    overall_percent = round(total_spent / total_budget * 100, 1) if total_budget > 0 else 0

    return BudgetSummary(
        year_month=year_month,
        total_budget=total_budget,
        total_spent=total_spent,
        overall_remaining=overall_remaining,
        overall_percent=overall_percent,
        is_over=total_spent > total_budget,
        categories=categories,
    )
