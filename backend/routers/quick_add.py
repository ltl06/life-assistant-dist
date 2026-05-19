"""快捷记录路由"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db, User, HealthRecord, FinanceRecord
from routers.auth import get_current_user
from datetime import date, datetime

router = APIRouter()

class QuickAddRequest(BaseModel):
    text: str

class QuickAddResponse(BaseModel):
    success: bool
    message: str
    type: str

def parse_quick_text(text: str, db, user_id):
    text = text.strip()
    original = text

    # 记账: "记账 50 餐饮" 或 "花了 30 买咖啡" 或 "+50 工资" 或 "-35 午餐"
    import re
    money_match = re.search(r'([+-]?)(\d+(?:\.\d{1,2})?)\s*(?:元|块)?', text)
    expense_keywords = ['花了', '消费', '支出', '买', '午餐', '晚餐', '早餐', '打车', '打车费', '停车', '外卖', '咖啡', '奶茶', '网购', '购物', '衣服', '话费', '日用品']
    income_keywords = ['工资', '收入', '奖金', '兼职', '外快', '投资收益', '理财']

    if money_match:
        amount = float(money_match.group(2))
        sign = money_match.group(1) or '+'
        rest = text[money_match.end():].strip()

        if '-' in sign or (sign == '+' and not income_keywords and expense_keywords):
            r_type = 'expense'
            for kw in expense_keywords:
                if kw in rest or kw in original:
                    break
            else:
                if '收入' in rest or '工资' in rest:
                    r_type = 'income'
        elif '+' in sign or any(kw in rest for kw in income_keywords):
            r_type = 'income'
        else:
            r_type = 'expense'

        cats = {
            '餐饮': ['午餐', '晚餐', '早餐', '外卖', '咖啡', '奶茶', '买', '吃饭'],
            '交通': ['打车', '打车费', '停车', '公交', '地铁', '加油'],
            '购物': ['网购', '购物', '衣服', '日用品'],
            '通讯': ['话费', '流量'],
            '工资': ['工资'],
            '奖金': ['奖金'],
            '兼职': ['兼职', '外快'],
        }

        category = rest if rest else '其他'
        for cat, kws in cats.items():
            if any(kw in original for kw in kws):
                category = cat
                break

        rec = FinanceRecord(
            user_id=user_id, type=r_type, amount=amount,
            category=category, date=date.today(),
        )
        db.add(rec)
        db.commit()
        label = "收入" if r_type == "income" else "支出"
        return QuickAddResponse(
            success=True,
            message=f"已记录 {label} ¥{amount}（{category}）",
            type="finance",
        )

    # 健康: "走了 8000 步" "体重 65" "睡了 7 小时"
    step_match = re.search(r'走了?\s*(\d+)\s*步', text)
    if step_match:
        steps = int(step_match.group(1))
        existing = db.query(HealthRecord).filter(
            HealthRecord.user_id == user_id,
            HealthRecord.date == date.today(),
        ).first()
        if existing:
            existing.steps = steps
        else:
            existing = HealthRecord(user_id=user_id, date=date.today(), steps=steps)
            db.add(existing)
        db.commit()
        return QuickAddResponse(
            success=True,
            message=f"已记录今日步数 {steps:,}",
            type="health",
        )

    weight_match = re.search(r'体重\s*(\d+(?:\.\d+)?)', text)
    if weight_match:
        weight = float(weight_match.group(1))
        existing = db.query(HealthRecord).filter(
            HealthRecord.user_id == user_id,
            HealthRecord.date == date.today(),
        ).first()
        if existing:
            existing.weight = weight
        else:
            existing = HealthRecord(user_id=user_id, date=date.today(), weight=weight)
            db.add(existing)
        db.commit()
        return QuickAddResponse(
            success=True,
            message=f"已记录体重 {weight} kg",
            type="health",
        )

    sleep_match = re.search(r'睡了?\s*(\d+(?:\.\d+)?)\s*(?:小时|h)?', text)
    if sleep_match:
        hours = float(sleep_match.group(1))
        existing = db.query(HealthRecord).filter(
            HealthRecord.user_id == user_id,
            HealthRecord.date == date.today(),
        ).first()
        if existing:
            existing.sleep_hours = hours
        else:
            existing = HealthRecord(user_id=user_id, date=date.today(), sleep_hours=hours)
            db.add(existing)
        db.commit()
        return QuickAddResponse(
            success=True,
            message=f"已记录睡眠 {hours} 小时",
            type="health",
        )

    return QuickAddResponse(
        success=False,
        message="无法识别内容。请尝试：「记账 35 午餐」「走了 8000 步」「体重 65」「睡了 7 小时」",
        type="unknown",
    )

@router.post("/quick-add", response_model=QuickAddResponse)
def quick_add(
    req: QuickAddRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return parse_quick_text(req.text, db, current_user.id)
