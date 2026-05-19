"""财务数据工具"""
from datetime import date, timedelta
from database import FinanceRecord

functions = [
    {
        "type": "function",
        "function": {
            "name": "log_finance",
            "description": "记录用户的收入或支出流水。",
            "parameters": {
                "type": "object",
                "properties": {
                    "record_date": {
                        "type": "string",
                        "description": "记录日期，格式 YYYY-MM-DD，默认为今天",
                    },
                    "type": {
                        "type": "string",
                        "description": "类型",
                        "enum": ["income", "expense"],
                    },
                    "amount": {
                        "type": "number",
                        "description": "金额（元）",
                        "minimum": 0,
                    },
                    "category": {
                        "type": "string",
                        "description": "分类（支出：餐饮/交通/购物/居住/医疗/教育/娱乐/通讯/服装/其他；收入：工资/奖金/投资收益/兼职/其他收入）",
                    },
                    "description": {
                        "type": "string",
                        "description": "备注说明",
                    },
                },
                "required": ["type", "amount", "category"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_finance_summary",
            "description": "获取用户近期的财务汇总，包括收支总额、各类别支出、结余。",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "查询天数，默认30天",
                        "default": 30,
                        "minimum": 1,
                        "maximum": 365,
                    },
                },
                "required": [],
            },
        },
    },
]

def execute(name: str, args: dict, db, user_id: int):
    if name == "log_finance":
        return _log_finance(args, db, user_id)
    if name == "get_finance_summary":
        return _get_summary(args, db, user_id)
    return {"error": f"未知工具: {name}"}

def _log_finance(args: dict, db, user_id: int):
    record_date = args.get("record_date")
    if record_date:
        record_date = date.fromisoformat(record_date)
    else:
        record_date = date.today()

    rec = FinanceRecord(
        user_id=user_id,
        type=args["type"],
        amount=args["amount"],
        category=args["category"],
        description=args.get("description"),
        date=record_date,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return {
        "success": True,
        "message": f"已记录{'收入' if args['type']=='income' else '支出'}：{args['amount']}元（{args['category']}）",
        "record_id": rec.id,
    }

def _get_summary(args: dict, db, user_id: int):
    days = args.get("days", 30)
    start = date.today() - timedelta(days=days)
    records = db.query(FinanceRecord).filter(
        FinanceRecord.user_id == user_id,
        FinanceRecord.date >= start,
    ).order_by(FinanceRecord.date.desc()).all()

    income = sum(r.amount for r in records if r.type == "income")
    expense = sum(r.amount for r in records if r.type == "expense")

    by_category = {}
    for r in records:
        if r.type == "expense":
            by_category[r.category] = by_category.get(r.category, 0) + r.amount

    return {
        "record_count": len(records),
        "total_income": round(income, 2),
        "total_expense": round(expense, 2),
        "balance": round(income - expense, 2),
        "expense_by_category": {k: round(v, 2) for k, v in sorted(by_category.items(), key=lambda x: -x[1])},
        "date_range": f"{start} 至 {date.today()}",
    }
