"""日记工具"""
from datetime import date, timedelta
from database import Diary

functions = [
    {
        "type": "function",
        "function": {
            "name": "create_diary",
            "description": "写一篇日记或情绪记录。",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "日记正文内容",
                    },
                    "title": {
                        "type": "string",
                        "description": "日记标题（可选）",
                    },
                    "mood": {
                        "type": "string",
                        "description": "当日心情",
                        "enum": ["开心", "平静", "一般", "低落", "焦虑", "疲惫", "兴奋"],
                    },
                    "tags": {
                        "type": "string",
                        "description": "标签，逗号分隔（如：工作,健康,家庭）",
                    },
                    "record_date": {
                        "type": "string",
                        "description": "日记日期，格式 YYYY-MM-DD（默认今天）",
                    },
                },
                "required": ["content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_diary_summary",
            "description": "获取用户近期日记汇总，包括写日记频率、情绪趋势、最新的日记。",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "查询天数，默认30天",
                        "default": 30,
                        "minimum": 1,
                    },
                },
                "required": [],
            },
        },
    },
]

def execute(name: str, args: dict, db, user_id: int):
    if name == "create_diary":
        return _create_diary(args, db, user_id)
    if name == "get_diary_summary":
        return _get_summary(args, db, user_id)
    return {"error": f"未知工具: {name}"}

def _create_diary(args: dict, db, user_id: int):
    record_date = date.today()
    if args.get("record_date"):
        record_date = date.fromisoformat(args["record_date"])

    d = Diary(
        user_id=user_id,
        title=args.get("title"),
        content=args["content"],
        mood=args.get("mood"),
        tags=args.get("tags"),
        date=record_date,
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    return {
        "success": True,
        "message": f"已保存日记（{record_date}）",
        "diary_id": d.id,
        "preview": args["content"][:50] + ("..." if len(args["content"]) > 50 else ""),
    }

def _get_summary(args: dict, db, user_id: int):
    days = args.get("days", 30)
    start = date.today() - timedelta(days=days)
    records = db.query(Diary).filter(
        Diary.user_id == user_id,
        Diary.date >= start,
    ).order_by(Diary.date.desc()).all()

    moods = {}
    for r in records:
        m = r.mood or "未记录"
        moods[m] = moods.get(m, 0) + 1

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

    latest = None
    if records:
        r = records[0]
        latest = {"date": r.date.isoformat(), "title": r.title, "mood": r.mood, "content_preview": r.content[:80] + ("..." if len(r.content) > 80 else "")}

    return {
        "total_count": len(records),
        "streak_days": streak,
        "mood_distribution": moods,
        "date_range": f"{start} 至 {date.today()}",
        "latest_diary": latest,
    }
