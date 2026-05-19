"""目标追踪工具 - 长期目标拆解与进度管理"""
from datetime import datetime, date, timedelta
import json

functions = [
    {
        "type": "function",
        "function": {
            "name": "create_goal",
            "description": "创建一个长期目标（如：减重10公斤、存够5万、跑完马拉松），系统会自动拆解为待办事项。",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "目标名称，如：减重到65公斤",
                    },
                    "description": {
                        "type": "string",
                        "description": "目标详细描述",
                    },
                    "target_date": {
                        "type": "string",
                        "description": "目标截止日期，格式 YYYY-MM-DD",
                    },
                    "category": {
                        "type": "string",
                        "description": "目标类别",
                        "enum": ["健康", "财务", "学习", "工作", "生活", "其他"],
                    },
                },
                "required": ["title", "target_date", "category"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_goals",
            "description": "查看用户所有目标及进度。",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "筛选状态",
                        "enum": ["active", "completed", "all"],
                        "default": "active",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_goal_progress",
            "description": "更新目标进度（0-100）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "goal_id": {
                        "type": "integer",
                        "description": "目标 ID",
                    },
                    "progress": {
                        "type": "integer",
                        "description": "进度百分比 0-100",
                    },
                    "note": {
                        "type": "string",
                        "description": "进度备注（如：本周完成了5次跑步）",
                    },
                },
                "required": ["goal_id", "progress"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_goal",
            "description": "删除一个目标。",
            "parameters": {
                "type": "object",
                "properties": {
                    "goal_id": {
                        "type": "integer",
                        "description": "目标 ID",
                    },
                },
                "required": ["goal_id"],
            },
        },
    },
]


def _ensure_table(db):
    from database import engine
    from sqlalchemy import text
    with engine.connect() as conn:
        tables = set(r[0] for r in conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall())
        if "goals" not in tables:
            conn.execute(text("""
                CREATE TABLE goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title VARCHAR NOT NULL,
                    description TEXT,
                    category VARCHAR,
                    target_date DATE,
                    progress INTEGER DEFAULT 0,
                    status VARCHAR DEFAULT 'active',
                    milestones TEXT,
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME
                )
            """))
            conn.commit()


def execute(name: str, args: dict, db, user_id: int):
    _ensure_table(db)
    if name == "create_goal":
        return _create_goal(args, db, user_id)
    if name == "get_goals":
        return _get_goals(args, db, user_id)
    if name == "update_goal_progress":
        return _update_progress(args, db, user_id)
    if name == "delete_goal":
        return _delete_goal(args, db, user_id)
    return {"error": f"未知工具: {name}"}


def _create_goal(args: dict, db, user_id: int):
    from database import engine
    from sqlalchemy import text

    title = args["title"]
    target_date = args["target_date"]
    category = args["category"]
    description = args.get("description", "")

    milestones = _generate_milestones(title, target_date, category)

    with engine.connect() as conn:
        result = conn.execute(
            text("""INSERT INTO goals (user_id, title, description, category, target_date, milestones)
                     VALUES (:uid, :title, :desc, :cat, :date, :milestones)"""),
            {
                "uid": user_id, "title": title, "desc": description,
                "cat": category, "date": target_date,
                "milestones": json.dumps(milestones, ensure_ascii=False),
            },
        )
        conn.commit()
        rid = result.lastrowid

    days_left = (datetime.fromisoformat(target_date) - datetime.now()).days
    return {
        "success": True,
        "message": f"已创建目标「{title}」，距离截止还有 {days_left} 天",
        "goal_id": rid,
        "milestones": milestones,
        "tip": "小周已自动生成了里程碑，你可以让小周根据里程碑创建待办事项",
    }


def _generate_milestones(title: str, target_date: str, category: str):
    end = datetime.fromisoformat(target_date)
    now = datetime.now()
    days = (end - now).days

    if days <= 0:
        return []

    if "减重" in title or "减肥" in title or "体重" in title:
        return [
            {"label": "设定阶段性目标", "progress": 10, "desc": "明确每周减重目标"},
            {"label": "制定饮食计划", "progress": 20, "desc": "记录每日热量摄入"},
            {"label": "开始运动计划", "progress": 40, "desc": "每周至少运动3次"},
            {"label": "坚持一个月", "progress": 60, "desc": "记录体重变化曲线"},
            {"label": "接近目标体重", "progress": 80, "desc": "到达目标体重的90%"},
            {"label": "达成目标", "progress": 100, "desc": "到达目标体重"},
        ]
    elif "存钱" in title or "储蓄" in title or "存款" in title:
        monthly = 3 if days >= 30 else 1
        milestones = []
        for i in range(monthly):
            pct = int((i + 1) / monthly * 100)
            milestones.append({
                "label": f"完成第{i+1}个月存款",
                "progress": pct,
                "desc": f"坚持第{i+1}个月储蓄计划",
            })
        return milestones
    elif "跑步" in title or "马拉松" in title or "运动" in title:
        return [
            {"label": "制定训练计划", "progress": 10, "desc": "设定每周跑步里程"},
            {"label": "开始基础训练", "progress": 25, "desc": "完成第1次5公里跑"},
            {"label": "提升耐力", "progress": 50, "desc": "完成10公里跑"},
            {"label": "挑战长距离", "progress": 75, "desc": "完成半马训练"},
            {"label": "达成目标", "progress": 100, "desc": "完成目标里程"},
        ]
    else:
        third = days // 3
        return [
            {"label": f"第一阶段（{min(third, 30)}天内）", "progress": 33, "desc": "完成基础准备工作"},
            {"label": f"第二阶段（{min(third*2, 60)}天内）", "progress": 66, "desc": "完成核心任务"},
            {"label": "达成目标", "progress": 100, "desc": "完成所有工作"},
        ]


def _get_goals(args: dict, db, user_id: int):
    from database import engine
    from sqlalchemy import text

    status_filter = args.get("status", "active")
    if status_filter == "active":
        where = "WHERE user_id=:uid AND status='active'"
    elif status_filter == "completed":
        where = "WHERE user_id=:uid AND status='completed'"
    else:
        where = "WHERE user_id=:uid"

    with engine.connect() as conn:
        rows = conn.execute(
            text(f"SELECT id, title, description, category, target_date, progress, status, milestones, notes FROM goals {where} ORDER BY created_at DESC"),
            {"uid": user_id},
        ).fetchall()

    goals = []
    now = datetime.now()
    for r in rows:
        target = datetime.fromisoformat(r[4]) if r[4] else None
        days_left = (target - now).days if target else None
        milestones = []
        try:
            milestones = json.loads(r[7]) if r[7] else []
        except:
            milestones = []

        goals.append({
            "id": r[0],
            "title": r[1],
            "description": r[2],
            "category": r[3],
            "target_date": r[4],
            "progress": r[5],
            "status": r[6],
            "milestones": milestones,
            "notes": r[8],
            "days_left": days_left if days_left is not None and days_left >= 0 else 0,
            "is_overdue": days_left is not None and days_left < 0,
        })

    active = [g for g in goals if g["status"] == "active"]
    completed = [g for g in goals if g["status"] == "completed"]
    return {
        "total": len(goals),
        "active_count": len(active),
        "completed_count": len(completed),
        "goals": goals,
    }


def _update_progress(args: dict, db, user_id: int):
    from database import engine
    from sqlalchemy import text

    progress = max(0, min(100, args["progress"]))
    note = args.get("note", "")

    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id, title, milestones FROM goals WHERE id=:id AND user_id=:uid"),
            {"id": args["goal_id"], "uid": user_id},
        ).fetchone()

        if not row:
            return {"error": "未找到该目标"}

        milestones = json.loads(row[2]) if row[2] else []
        status = "completed" if progress >= 100 else "active"

        existing_notes = []
        try:
            existing = conn.execute(
                text("SELECT notes FROM goals WHERE id=:id"),
                {"id": args["goal_id"]},
            ).fetchone()
            if existing and existing[0]:
                existing_notes = json.loads(existing[0])
        except:
            pass

        if note:
            existing_notes.append({
                "date": datetime.now().isoformat(),
                "progress": progress,
                "note": note,
            })

        conn.execute(
            text("UPDATE goals SET progress=:p, status=:s, notes=:n, updated_at=:now WHERE id=:id"),
            {
                "p": progress, "s": status, "n": json.dumps(existing_notes, ensure_ascii=False),
                "now": datetime.now().isoformat(), "id": args["goal_id"],
            },
        )
        conn.commit()

    msg = f"目标「{row[1]}」进度已更新为 {progress}%"
    if progress >= 100:
        msg += "，恭喜达成目标！"
    return {"success": True, "message": msg, "progress": progress, "status": status}


def _delete_goal(args: dict, db, user_id: int):
    from database import engine
    from sqlalchemy import text

    with engine.connect() as conn:
        result = conn.execute(
            text("DELETE FROM goals WHERE id=:id AND user_id=:uid"),
            {"id": args["goal_id"], "uid": user_id},
        )
        conn.commit()
    return {
        "success": True,
        "message": "目标已删除" if result.rowcount > 0 else "未找到该目标",
    }
