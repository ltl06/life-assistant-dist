"""用户设置工具"""
from database import User

functions = [
    {
        "type": "function",
        "function": {
            "name": "update_user_location",
            "description": "更新用户所在城市，用于天气显示等功能。",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如：北京、上海、广州、深圳",
                    },
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_profile",
            "description": "获取当前用户的个人资料信息。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]


def execute(name: str, args: dict, db, user_id: int):
    if name == "update_user_location":
        return _update_location(args, db, user_id)
    if name == "get_user_profile":
        return _get_profile(args, db, user_id)
    return {"error": f"未知工具: {name}"}


def _update_location(args: dict, db, user_id: int):
    city = args.get("city", "").strip()
    if not city:
        return {"error": "城市名称不能为空"}

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": "用户不存在"}

    user.location = city
    db.commit()
    return {
        "success": True,
        "message": f"已更新所在城市为 {city}，天气将显示该城市数据",
        "city": city,
    }


def _get_profile(args: dict, db, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": "用户不存在"}

    return {
        "username": user.username,
        "email": user.email,
        "location": user.location or "未设置",
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }
