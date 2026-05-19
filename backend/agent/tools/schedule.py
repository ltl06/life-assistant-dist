"""日程待办工具"""
from datetime import datetime, date
from database import Todo

functions = [
    {
        "type": "function",
        "function": {
            "name": "create_todo",
            "description": "创建一个新的待办事项。",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "待办标题",
                    },
                    "description": {
                        "type": "string",
                        "description": "详细描述（可选）",
                    },
                    "priority": {
                        "type": "string",
                        "description": "优先级",
                        "enum": ["low", "medium", "high"],
                        "default": "medium",
                    },
                    "due_date": {
                        "type": "string",
                        "description": "截止日期，格式 YYYY-MM-DD（可选）",
                    },
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_todo",
            "description": "更新待办事项状态（标记完成/未完成）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "todo_id": {
                        "type": "integer",
                        "description": "待办事项 ID",
                    },
                    "completed": {
                        "type": "boolean",
                        "description": "是否完成",
                    },
                    "title": {
                        "type": "string",
                        "description": "新标题（可选）",
                    },
                },
                "required": ["todo_id", "completed"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_todo",
            "description": "删除一个待办事项。",
            "parameters": {
                "type": "object",
                "properties": {
                    "todo_id": {
                        "type": "integer",
                        "description": "待办事项 ID",
                    },
                },
                "required": ["todo_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_todos",
            "description": "查询用户的待办事项列表。",
            "parameters": {
                "type": "object",
                "properties": {
                    "completed": {
                        "type": "boolean",
                        "description": "筛选状态（不填则返回全部）",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量上限，默认50",
                        "default": 50,
                    },
                },
                "required": [],
            },
        },
    },
]

def execute(name: str, args: dict, db, user_id: int):
    if name == "create_todo":
        return _create_todo(args, db, user_id)
    if name == "update_todo":
        return _update_todo(args, db, user_id)
    if name == "delete_todo":
        return _delete_todo(args, db, user_id)
    if name == "get_todos":
        return _get_todos(args, db, user_id)
    return {"error": f"未知工具: {name}"}

def _create_todo(args: dict, db, user_id: int):
    due = None
    if args.get("due_date"):
        due = datetime.fromisoformat(args["due_date"])
    t = Todo(
        user_id=user_id,
        title=args["title"],
        description=args.get("description"),
        priority=args.get("priority", "medium"),
        due_date=due,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return {
        "success": True,
        "message": f"已创建待办：{args['title']}",
        "todo_id": t.id,
        "todo": {"id": t.id, "title": t.title, "completed": t.completed, "priority": t.priority},
    }

def _update_todo(args: dict, db, user_id: int):
    t = db.query(Todo).filter(Todo.id == args["todo_id"], Todo.user_id == user_id).first()
    if not t:
        return {"error": "未找到该待办"}
    if "title" in args:
        t.title = args["title"]
    t.completed = args["completed"]
    db.commit()
    status = "已完成" if args["completed"] else "已标记为未完成"
    return {"success": True, "message": f"待办「{t.title}」{status}", "todo_id": t.id}

def _delete_todo(args: dict, db, user_id: int):
    t = db.query(Todo).filter(Todo.id == args["todo_id"], Todo.user_id == user_id).first()
    if not t:
        return {"error": "未找到该待办"}
    db.delete(t)
    db.commit()
    return {"success": True, "message": f"已删除待办"}

def _get_todos(args: dict, db, user_id: int):
    q = db.query(Todo).filter(Todo.user_id == user_id)
    if "completed" in args and args["completed"] is not None:
        q = q.filter(Todo.completed == args["completed"])
    todos = q.order_by(Todo.created_at.desc()).limit(args.get("limit", 50)).all()
    return {
        "count": len(todos),
        "todos": [
            {"id": t.id, "title": t.title, "completed": t.completed, "priority": t.priority, "due_date": t.due_date.isoformat() if t.due_date else None}
            for t in todos
        ],
    }
