"""预算管理工具"""
from datetime import date
from sqlalchemy import func

functions = [
    {
        "type": "function",
        "function": {
            "name": "create_budget",
            "description": "为某个月份设置某个支出类别的预算上限。",
            "parameters": {
                "type": "object",
                "properties": {
                    "year_month": {
                        "type": "string",
                        "description": "预算月份，格式 YYYY-MM，如 2026-05",
                    },
                    "category": {
                        "type": "string",
                        "description": "支出类别",
                        "enum": ["餐饮", "交通", "购物", "居住", "医疗", "教育", "娱乐", "通讯", "服装", "其他"],
                    },
                    "budget_amount": {
                        "type": "number",
                        "description": "预算金额（元）",
                    },
                },
                "required": ["year_month", "category", "budget_amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_budget_status",
            "description": "查看某个月份的预算执行情况，了解各分类已花费和剩余预算。",
            "parameters": {
                "type": "object",
                "properties": {
                    "year_month": {
                        "type": "string",
                        "description": "预算月份，格式 YYYY-MM，默认本月",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_budget",
            "description": "删除某个月份的某个分类预算。",
            "parameters": {
                "type": "object",
                "properties": {
                    "budget_id": {
                        "type": "integer",
                        "description": "预算记录 ID",
                    },
                },
                "required": ["budget_id"],
            },
        },
    },
]


def execute(name: str, args: dict, db, user_id: int):
    if name == "create_budget":
        return _create_budget(args, db, user_id)
    if name == "get_budget_status":
        return _get_budget_status(args, db, user_id)
    if name == "delete_budget":
        return _delete_budget(args, db, user_id)
    return {"error": f"未知工具: {name}"}


def _create_budget(args: dict, db, user_id: int):
    from database import Budget, FinanceRecord

    year_month = args["year_month"]
    category = args["category"]
    budget_amount = args["budget_amount"]

    existing = db.query(Budget).filter(
        Budget.user_id == user_id,
        Budget.year_month == year_month,
        Budget.category == category,
    ).first()

    if existing:
        existing.budget_amount = budget_amount
        db.commit()
        return {
            "success": True,
            "message": f"已更新 {year_month} {category} 预算为 {budget_amount} 元",
            "budget_id": existing.id,
        }

    b = Budget(
        user_id=user_id,
        year_month=year_month,
        category=category,
        budget_amount=budget_amount,
    )
    db.add(b)
    db.commit()
    db.refresh(b)
    return {
        "success": True,
        "message": f"已为 {year_month} {category} 设置预算 {budget_amount} 元",
        "budget_id": b.id,
    }


def _get_budget_status(args: dict, db, user_id: int):
    from database import Budget, FinanceRecord

    year_month = args.get("year_month")
    if not year_month:
        today = date.today()
        year_month = f"{today.year}-{today.month:02d}"

    budgets = db.query(Budget).filter(
        Budget.user_id == user_id,
        Budget.year_month == year_month,
    ).all()

    if not budgets:
        return {
            "year_month": year_month,
            "total_budget": 0,
            "total_spent": 0,
            "remaining": 0,
            "status": "no_budget",
            "message": f"{year_month} 尚未设置任何预算",
        }

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
        FinanceRecord.user_id == user_id,
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
        status = "over" if spent > b.budget_amount else ("warning" if percent > 80 else "ok")
        categories.append({
            "category": b.category,
            "budget": b.budget_amount,
            "spent": round(spent, 2),
            "remaining": round(remaining, 2),
            "percent": percent,
            "status": status,
        })

    total_budget = sum(b.budget_amount for b in budgets)
    return {
        "year_month": year_month,
        "total_budget": total_budget,
        "total_spent": round(total_spent, 2),
        "remaining": round(total_budget - total_spent, 2),
        "overall_percent": round(total_spent / total_budget * 100, 1) if total_budget > 0 else 0,
        "categories": categories,
    }


def _delete_budget(args: dict, db, user_id: int):
    from database import Budget

    b = db.query(Budget).filter(
        Budget.id == args["budget_id"],
        Budget.user_id == user_id,
    ).first()
    if not b:
        return {"error": "未找到该预算记录"}
    db.delete(b)
    db.commit()
    return {"success": True, "message": f"已删除 {b.year_month} {b.category} 预算"}
