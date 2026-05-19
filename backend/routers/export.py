"""数据导出路由"""
import csv
import io
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db, User, HealthRecord, FinanceRecord, Diary, Todo, Habit
from routers.auth import get_current_user

router = APIRouter()

@router.get("/health")
def export_health(
    days: int = 90,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from datetime import timedelta
    start = datetime.utcnow().date() - timedelta(days=days)
    records = db.query(HealthRecord).filter(
        HealthRecord.user_id == current_user.id,
        HealthRecord.date >= start,
    ).order_by(HealthRecord.date.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["日期", "体重(kg)", "步数", "睡眠时长(h)", "心情", "备注"])
    for r in records:
        writer.writerow([
            r.date.isoformat() if r.date else "",
            r.weight or "",
            r.steps or 0,
            r.sleep_hours or "",
            r.mood or "",
            r.notes or "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=health_{datetime.utcnow().strftime('%Y%m%d')}.csv"},
    )

@router.get("/finance")
def export_finance(
    days: int = 90,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from datetime import timedelta
    start = datetime.utcnow().date() - timedelta(days=days)
    records = db.query(FinanceRecord).filter(
        FinanceRecord.user_id == current_user.id,
        FinanceRecord.date >= start,
    ).order_by(FinanceRecord.date.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["日期", "类型", "金额", "分类", "备注"])
    for r in records:
        writer.writerow([
            r.date.isoformat() if r.date else "",
            "收入" if r.type == "income" else "支出",
            r.amount,
            r.category,
            r.description or "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=finance_{datetime.utcnow().strftime('%Y%m%d')}.csv"},
    )

@router.get("/diary")
def export_diary(
    days: int = 90,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from datetime import timedelta
    start = datetime.utcnow().date() - timedelta(days=days)
    records = db.query(Diary).filter(
        Diary.user_id == current_user.id,
        Diary.date >= start,
    ).order_by(Diary.date.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["日期", "标题", "心情", "标签", "内容"])
    for r in records:
        writer.writerow([
            r.date.isoformat() if r.date else "",
            r.title or "",
            r.mood or "",
            r.tags or "",
            r.content,
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=diary_{datetime.utcnow().strftime('%Y%m%d')}.csv"},
    )

@router.get("/todos")
def export_todos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    records = db.query(Todo).filter(
        Todo.user_id == current_user.id,
    ).order_by(Todo.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["标题", "描述", "优先级", "完成状态", "截止日期", "创建时间"])
    for r in records:
        writer.writerow([
            r.title,
            r.description or "",
            r.priority,
            "已完成" if r.completed else "未完成",
            r.due_date.strftime("%Y-%m-%d %H:%M") if r.due_date else "",
            r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=todos_{datetime.utcnow().strftime('%Y%m%d')}.csv"},
    )
