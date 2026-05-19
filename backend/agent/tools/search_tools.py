"""全局搜索工具 - 跨模块搜索用户的各类数据"""
from datetime import date, timedelta

functions = [
    {
        "type": "function",
        "function": {
            "name": "search_all",
            "description": "在健康、财务、日记、待办、习惯等所有模块中全局搜索关键词。适合用户想找某条记录但不确定在哪个模块时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "搜索关键词，如：跑步、午餐、日记标题中的词",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "每个模块最多返回条数，默认 5",
                        "default": 5,
                    },
                },
                "required": ["keyword"],
            },
        },
    },
]


def execute(name: str, args: dict, db, user_id: int):
    if name == "search_all":
        return _search_all(args, db, user_id)
    return {"error": f"未知工具: {name}"}


def _search_all(args: dict, db, user_id: int):
    from database import (
        HealthRecord, FinanceRecord, Diary, Todo, Habit, HabitCheckin,
    )

    keyword = args.get("keyword", "").strip()
    limit = args.get("limit", 5)
    if not keyword:
        return {"error": "请提供搜索关键词"}

    kw_lower = keyword.lower()
    results = {}

    # 健康记录
    health = db.query(HealthRecord).filter(
        HealthRecord.user_id == user_id,
    ).order_by(HealthRecord.date.desc()).limit(limit * 2).all()
    health_hits = [
        {
            "module": "健康",
            "date": str(h.date),
            "content": f"步数:{h.steps} 睡眠:{h.sleep_hours}h 体重:{h.weight}kg 心情:{h.mood or '未记录'}",
            "notes": h.notes,
        }
        for h in health
        if any(
            kw_lower in str(v).lower()
            for v in [h.notes, h.mood, str(h.date)]
            if v
        )
    ][:limit]
    if health_hits:
        results["健康"] = health_hits

    # 财务记录
    finance = db.query(FinanceRecord).filter(
        FinanceRecord.user_id == user_id,
    ).order_by(FinanceRecord.date.desc()).limit(limit * 2).all()
    finance_hits = [
        {
            "module": "财务",
            "date": str(f.date),
            "content": f"{'支出' if f.type == 'expense' else '收入'} {f.amount}元 [{f.category}] {f.description or ''}",
        }
        for f in finance
        if kw_lower in (f.description or "").lower() or kw_lower in f.category.lower()
    ][:limit]
    if finance_hits:
        results["财务"] = finance_hits

    # 日记
    diaries = db.query(Diary).filter(
        Diary.user_id == user_id,
    ).order_by(Diary.date.desc()).limit(limit * 2).all()
    diary_hits = [
        {
            "module": "日记",
            "date": str(d.date),
            "title": d.title,
            "content": d.content[:100] + ("..." if len(d.content) > 100 else ""),
            "mood": d.mood,
        }
        for d in diaries
        if kw_lower in (d.title or "").lower() or kw_lower in d.content.lower() or kw_lower in (d.tags or "").lower()
    ][:limit]
    if diary_hits:
        results["日记"] = diary_hits

    # 待办
    todos = db.query(Todo).filter(
        Todo.user_id == user_id,
    ).order_by(Todo.created_at.desc()).limit(limit * 2).all()
    todo_hits = [
        {
            "module": "待办",
            "content": t.title,
            "description": t.description,
            "status": "已完成" if t.completed else "进行中",
            "priority": t.priority,
        }
        for t in todos
        if kw_lower in (t.title or "").lower() or kw_lower in (t.description or "").lower()
    ][:limit]
    if todo_hits:
        results["待办"] = todo_hits

    # 习惯
    habits = db.query(Habit).filter(Habit.user_id == user_id).all()
    habit_hits = []
    for h in habits:
        if kw_lower in h.name.lower():
            habit_hits.append({
                "module": "习惯",
                "name": h.name,
                "frequency": h.frequency,
                "streak": h.current_streak,
            })
    if habit_hits:
        results["习惯"] = habit_hits[:limit]

    total = sum(len(v) for v in results.values())
    if total == 0:
        return {
            "keyword": keyword,
            "total": 0,
            "message": f"未找到包含「{keyword}」的记录",
        }

    return {
        "keyword": keyword,
        "total": total,
        "module_count": len(results),
        "results": results,
        "message": f"在 {len(results)} 个模块中找到 {total} 条相关记录",
    }
