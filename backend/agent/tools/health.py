"""健康数据工具"""
from datetime import date, timedelta
from database import HealthRecord

functions = [
    {
        "type": "function",
        "function": {
            "name": "log_health",
            "description": "记录用户的健康数据（运动步数、睡眠时长、体重、心情）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "record_date": {
                        "type": "string",
                        "description": "记录日期，格式 YYYY-MM-DD，默认为今天",
                        "default": None,
                    },
                    "steps": {
                        "type": "integer",
                        "description": "当日步数",
                        "minimum": 0,
                    },
                    "sleep_hours": {
                        "type": "number",
                        "description": "睡眠时长（小时）",
                        "minimum": 0,
                        "maximum": 24,
                    },
                    "weight": {
                        "type": "number",
                        "description": "体重（kg）",
                        "minimum": 20,
                        "maximum": 300,
                    },
                    "mood": {
                        "type": "string",
                        "description": "心情",
                        "enum": ["开心", "平静", "一般", "低落", "焦虑", "疲惫", "兴奋"],
                    },
                    "notes": {
                        "type": "string",
                        "description": "备注说明",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_health_summary",
            "description": "获取用户近期的健康数据汇总，包括平均步数、睡眠、体重等趋势。",
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
    if name == "log_health":
        return _log_health(args, db, user_id)
    if name == "get_health_summary":
        return _get_summary(args, db, user_id)
    return {"error": f"未知工具: {name}"}

def _log_health(args: dict, db, user_id: int):
    record_date = args.get("record_date")
    if record_date:
        record_date = date.fromisoformat(record_date)
    else:
        record_date = date.today()

    existing = db.query(HealthRecord).filter(
        HealthRecord.user_id == user_id,
        HealthRecord.date == record_date,
    ).first()

    if existing:
        if "steps" in args and args["steps"] is not None:
            existing.steps = args["steps"]
        if "sleep_hours" in args and args["sleep_hours"] is not None:
            existing.sleep_hours = args["sleep_hours"]
        if "weight" in args and args["weight"] is not None:
            existing.weight = args["weight"]
        if "mood" in args and args["mood"] is not None:
            existing.mood = args["mood"]
        if "notes" in args and args["notes"] is not None:
            existing.notes = args["notes"]
        db.commit()
        return {"success": True, "message": f"已更新 {record_date} 的健康记录", "record_id": existing.id}

    rec = HealthRecord(
        user_id=user_id,
        date=record_date,
        steps=args.get("steps") or 0,
        sleep_hours=args.get("sleep_hours"),
        weight=args.get("weight"),
        mood=args.get("mood"),
        notes=args.get("notes"),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return {"success": True, "message": f"已记录 {record_date} 的健康数据", "record_id": rec.id}

def _get_summary(args: dict, db, user_id: int):
    days = args.get("days", 30)
    start = date.today() - timedelta(days=days)
    records = db.query(HealthRecord).filter(
        HealthRecord.user_id == user_id,
        HealthRecord.date >= start,
    ).order_by(HealthRecord.date.desc()).all()

    if not records:
        return {"summary": "暂无健康数据", "record_count": 0}

    weights = [r.weight for r in records if r.weight]
    sleeps = [r.sleep_hours for r in records if r.sleep_hours]
    steps = [r.steps for r in records if r.steps]
    moods = {}
    for r in records:
        if r.mood:
            moods[r.mood] = moods.get(r.mood, 0) + 1

    summary = {
        "record_count": len(records),
        "avg_steps": round(sum(steps) / len(steps)) if steps else None,
        "avg_sleep": round(sum(sleeps) / len(sleeps), 1) if sleeps else None,
        "avg_weight": round(sum(weights) / len(weights), 1) if weights else None,
        "latest_weight": weights[0] if weights else None,
        "mood_distribution": moods,
        "date_range": f"{start} 至 {date.today()}",
    }
    return summary
