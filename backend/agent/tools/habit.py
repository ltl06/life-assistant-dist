"""习惯追踪工具"""
from datetime import date, timedelta
from database import Habit, HabitCheckin

functions = [
    {
        "type": "function",
        "function": {
            "name": "create_habit",
            "description": "创建一个新的习惯追踪目标。",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "习惯名称（如：每天跑步、早起、读书）",
                    },
                    "frequency": {
                        "type": "string",
                        "description": "频率",
                        "enum": ["daily", "weekly", "monthly"],
                        "default": "daily",
                    },
                    "target": {
                        "type": "integer",
                        "description": "每日目标次数（默认1）",
                        "default": 1,
                        "minimum": 1,
                    },
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "checkin_habit",
            "description": "对某个习惯进行打卡。",
            "parameters": {
                "type": "object",
                "properties": {
                    "habit_id": {
                        "type": "integer",
                        "description": "习惯 ID",
                    },
                    "check_date": {
                        "type": "string",
                        "description": "打卡日期，格式 YYYY-MM-DD（默认今天）",
                    },
                },
                "required": ["habit_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_habit_summary",
            "description": "获取用户的习惯追踪汇总，包括所有习惯、连续打卡天数。",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "查询天数，默认30天",
                        "default": 30,
                    },
                },
                "required": [],
            },
        },
    },
]

def execute(name: str, args: dict, db, user_id: int):
    if name == "create_habit":
        return _create_habit(args, db, user_id)
    if name == "checkin_habit":
        return _checkin_habit(args, db, user_id)
    if name == "get_habit_summary":
        return _get_summary(args, db, user_id)
    return {"error": f"未知工具: {name}"}

def _create_habit(args: dict, db, user_id: int):
    h = Habit(
        user_id=user_id,
        name=args["name"],
        frequency=args.get("frequency", "daily"),
        target=args.get("target", 1),
    )
    db.add(h)
    db.commit()
    db.refresh(h)
    return {
        "success": True,
        "message": f"已创建习惯：{args['name']}",
        "habit_id": h.id,
        "habit": {"id": h.id, "name": h.name, "frequency": h.frequency, "streak": 0},
    }

def _checkin_habit(args: dict, db, user_id: int):
    check_date = date.today()
    if args.get("check_date"):
        check_date = date.fromisoformat(args["check_date"])

    existing = db.query(HabitCheckin).filter(
        HabitCheckin.habit_id == args["habit_id"],
        HabitCheckin.user_id == user_id,
        HabitCheckin.date == check_date,
    ).first()
    if existing:
        return {"already_checked": True, "message": f"{check_date} 已打卡，无需重复打卡"}

    checkin = HabitCheckin(user_id=user_id, habit_id=args["habit_id"], date=check_date)
    db.add(checkin)
    _recalc_streak(db, user_id, args["habit_id"])
    db.commit()

    habit = db.query(Habit).filter(Habit.id == args["habit_id"], Habit.user_id == user_id).first()
    return {
        "success": True,
        "message": f"打卡成功！当前连续 {habit.current_streak} 天",
        "streak": habit.current_streak,
    }

def _recalc_streak(db, user_id: int, habit_id: int):
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

def _get_summary(args: dict, db, user_id: int):
    days = args.get("days", 30)
    start = date.today() - timedelta(days=days)
    habits = db.query(Habit).filter(Habit.user_id == user_id).all()
    result = []
    for h in habits:
        recent = db.query(HabitCheckin).filter(
            HabitCheckin.habit_id == h.id,
            HabitCheckin.user_id == user_id,
            HabitCheckin.date >= start,
        ).count()
        result.append({
            "id": h.id,
            "name": h.name,
            "frequency": h.frequency,
            "current_streak": h.current_streak,
            "checkins_last_{}".format(days): recent,
        })
    return {
        "habit_count": len(result),
        "habits": result,
    }
