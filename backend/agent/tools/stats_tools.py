"""统计汇总工具 - 一次性给出用户所有模块的关键指标"""
from datetime import date, timedelta

functions = [
    {
        "type": "function",
        "function": {
            "name": "get_overall_stats",
            "description": "一次性获取用户在所有模块（健康、财务、习惯、日记）的关键统计数据，适合做整体回顾或给用户一个生活状态全景。",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "统计天数，默认 30 天",
                        "default": 30,
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_today_summary",
            "description": "获取用户今日所有数据的快速汇总：今日健康记录、财务记录、待办完成情况、习惯打卡情况。适合每天早晨快速了解自己的一天起点。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]


def execute(name: str, args: dict, db, user_id: int):
    if name == "get_overall_stats":
        return _get_overall(args, db, user_id)
    if name == "get_today_summary":
        return _get_today(args, db, user_id)
    return {"error": f"未知工具: {name}"}


def _get_overall(args: dict, db, user_id: int):
    from database import HealthRecord, FinanceRecord, Diary, Habit, HabitCheckin, Todo

    days = args.get("days", 30)
    start = date.today() - timedelta(days=days)

    health = db.query(HealthRecord).filter(
        HealthRecord.user_id == user_id, HealthRecord.date >= start
    ).all()
    finance = db.query(FinanceRecord).filter(
        FinanceRecord.user_id == user_id, FinanceRecord.date >= start
    ).all()
    diaries = db.query(Diary).filter(
        Diary.user_id == user_id, Diary.date >= start
    ).all()
    habits = db.query(Habit).filter(Habit.user_id == user_id).all()
    todos = db.query(Todo).filter(Todo.user_id == user_id).all()

    # 健康
    steps = [r.steps for r in health if r.steps]
    sleeps = [r.sleep_hours for r in health if r.sleep_hours]
    weights = [r.weight for r in health if r.weight]
    moods = {}
    for r in health:
        if r.mood:
            moods[r.mood] = moods.get(r.mood, 0) + 1

    # 财务
    income = sum(r.amount for r in finance if r.type == "income")
    expense = sum(r.amount for r in finance if r.type == "expense")
    by_cat = {}
    for r in finance:
        if r.type == "expense":
            by_cat[r.category] = by_cat.get(r.category, 0) + r.amount

    # 习惯
    habit_stats = []
    for h in habits:
        recent = db.query(HabitCheckin).filter(
            HabitCheckin.habit_id == h.id, HabitCheckin.date >= start
        ).count()
        habit_stats.append({"name": h.name, "streak": h.current_streak, "checkins": recent})

    # 日记
    diary_moods = {}
    for d in diaries:
        m = d.mood or "未记录"
        diary_moods[m] = diary_moods.get(m, 0) + 1

    # 待办
    completed_todos = sum(1 for t in todos if t.completed)
    active_todos = sum(1 for t in todos if not t.completed)

    return {
        "period_days": days,
        "date_range": f"{start} 至 {date.today()}",
        "health": {
            "record_count": len(health),
            "avg_steps": round(sum(steps) / len(steps)) if steps else 0,
            "avg_sleep": round(sum(sleeps) / len(sleeps), 1) if sleeps else None,
            "avg_weight": round(sum(weights) / len(weights), 1) if weights else None,
            "mood_distribution": moods,
        },
        "finance": {
            "record_count": len(finance),
            "total_income": round(income, 2),
            "total_expense": round(expense, 2),
            "balance": round(income - expense, 2),
            "top_expense": max(by_cat, key=by_cat.get) if by_cat else None,
            "expense_by_category": {k: round(v, 2) for k, v in sorted(by_cat.items(), key=lambda x: -x[1])},
        },
        "habits": {
            "total": len(habits),
            "active": habit_stats,
        },
        "diary": {
            "record_count": len(diaries),
            "mood_distribution": diary_moods,
        },
        "todos": {
            "total": len(todos),
            "completed": completed_todos,
            "active": active_todos,
        },
    }


def _get_today(args: dict, db, user_id: int):
    from database import HealthRecord, FinanceRecord, Todo, Habit, HabitCheckin

    today = date.today()

    # 健康
    h = db.query(HealthRecord).filter(
        HealthRecord.user_id == user_id, HealthRecord.date == today
    ).first()

    # 财务
    finance_today = db.query(FinanceRecord).filter(
        FinanceRecord.user_id == user_id, FinanceRecord.date == today
    ).all()

    # 待办
    todos_today = db.query(Todo).filter(Todo.user_id == user_id).all()
    active_todos = [t for t in todos_today if not t.completed]

    # 习惯打卡
    checkins_today = db.query(HabitCheckin).filter(
        HabitCheckin.user_id == user_id, HabitCheckin.date == today
    ).all()
    checked_ids = {c.habit_id for c in checkins_today}

    all_habits = db.query(Habit).filter(Habit.user_id == user_id).all()
    habit_status = [
        {
            "name": h.name,
            "checked": h.id in checked_ids,
            "streak": h.current_streak,
        }
        for h in all_habits
    ]

    return {
        "date": str(today),
        "health": {
            "recorded": h is not None,
            "steps": h.steps if h and h.steps else None,
            "sleep": h.sleep_hours if h else None,
            "weight": h.weight if h else None,
            "mood": h.mood if h else None,
        },
        "finance": {
            "count": len(finance_today),
            "income": sum(r.amount for r in finance_today if r.type == "income"),
            "expense": sum(r.amount for r in finance_today if r.type == "expense"),
        },
        "todos": {
            "total_active": len(active_todos),
            "completed_today": sum(1 for t in todos_today if t.completed),
            "top_3": [{"title": t.title, "priority": t.priority} for t in active_todos[:3]],
        },
        "habits": {
            "total": len(all_habits),
            "checked_today": len(checkins_today),
            "details": habit_status,
        },
    }
