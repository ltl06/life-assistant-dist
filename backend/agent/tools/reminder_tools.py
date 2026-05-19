"""提醒工具 - 设定和管理各类提醒"""
from datetime import datetime, timedelta
import json

functions = [
    {
        "type": "function",
        "function": {
            "name": "create_reminder",
            "description": "创建一个提醒事项。",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "提醒标题",
                    },
                    "remind_at": {
                        "type": "string",
                        "description": "提醒时间，格式 YYYY-MM-DD HH:MM",
                    },
                    "note": {
                        "type": "string",
                        "description": "附加说明（可选）",
                    },
                },
                "required": ["title", "remind_at"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_reminders",
            "description": "查看所有提醒列表。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_reminder",
            "description": "删除一个提醒。",
            "parameters": {
                "type": "object",
                "properties": {
                    "reminder_id": {
                        "type": "integer",
                        "description": "提醒 ID",
                    },
                },
                "required": ["reminder_id"],
            },
        },
    },
]


def execute(name: str, args: dict, db, user_id: int):
    if name == "create_reminder":
        return _create_reminder(args, db, user_id)
    if name == "get_reminders":
        return _get_reminders(args, db, user_id)
    if name == "delete_reminder":
        return _delete_reminder(args, db, user_id)
    return {"error": f"未知工具: {name}"}


def _ensure_reminder_table(db):
    from database import engine
    from sqlalchemy import text
    with engine.connect() as conn:
        tables = set(r[0] for r in conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall())
        if "reminders" not in tables:
            conn.execute(text("""
                CREATE TABLE reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title VARCHAR NOT NULL,
                    remind_at DATETIME NOT NULL,
                    note TEXT,
                    triggered INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()


def _create_reminder(args: dict, db, user_id: int):
    _ensure_reminder_table(db)

    title = args.get("title", "").strip()
    remind_at_str = args.get("remind_at", "").strip()
    note = args.get("note", "").strip()

    if not title or not remind_at_str:
        return {"error": "标题和提醒时间均不能为空"}

    try:
        remind_at = datetime.fromisoformat(remind_at_str)
    except ValueError:
        return {"error": f"时间格式错误，请使用 YYYY-MM-DD HH:MM 格式，如 2026-05-20 09:00"}

    from database import engine
    from sqlalchemy import text
    with engine.connect() as conn:
        conn.execute(
            text("INSERT INTO reminders (user_id, title, remind_at, note) VALUES (:uid, :title, :at, :note)"),
            {"uid": user_id, "title": title, "at": remind_at.isoformat(), "note": note},
        )
        conn.commit()
        rid = conn.execute(text("SELECT last_insert_rowid()")).fetchone()[0]

    return {
        "success": True,
        "message": f"已设置提醒：{title}，时间：{remind_at.strftime('%Y-%m-%d %H:%M')}",
        "reminder_id": rid,
    }


def _get_reminders(args: dict, db, user_id: int):
    _ensure_reminder_table(db)

    from database import engine
    from sqlalchemy import text
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, title, remind_at, note, triggered FROM reminders WHERE user_id=:uid ORDER BY remind_at ASC LIMIT 50"),
            {"uid": user_id},
        ).fetchall()

    reminders = []
    now = datetime.now()
    for r in rows:
        remind_at = datetime.fromisoformat(r[2]) if isinstance(r[2], str) else r[2]
        status = "已过期" if remind_at < now else "待提醒"
        reminders.append({
            "id": r[0],
            "title": r[1],
            "remind_at": r[2],
            "note": r[3],
            "status": status,
        })

    return {
        "count": len(reminders),
        "reminders": reminders,
    }


def _delete_reminder(args: dict, db, user_id: int):
    _ensure_reminder_table(db)

    from database import engine
    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(
            text("DELETE FROM reminders WHERE id=:id AND user_id=:uid"),
            {"id": args["reminder_id"], "uid": user_id},
        )
        conn.commit()

    return {
        "success": True,
        "message": "提醒已删除" if result.rowcount > 0 else "未找到该提醒",
    }
