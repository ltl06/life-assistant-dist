"""Agent 工具注册表"""
from agent.tools import (
    health, finance, schedule, habit, diary, weather, budget_tools,
    settings_tools, search_tools, reminder_tools, stats_tools,
    goals_tools, report_tools, command_tools,
)
from agent.core import get_memory_tools, _do_remember_memory, _do_recall_memory

ALL_TOOLS = [
    *health.functions,
    *finance.functions,
    *schedule.functions,
    *habit.functions,
    *diary.functions,
    *weather.functions,
    *budget_tools.functions,
    *settings_tools.functions,
    *search_tools.functions,
    *reminder_tools.functions,
    *stats_tools.functions,
    *goals_tools.functions,
    *report_tools.functions,
    *command_tools.functions,
    *get_memory_tools(),
]

def execute_tool(name: str, arguments: dict, db, user_id: int):
    """根据工具名路由到具体实现"""
    ns = {
        "log_health": health,
        "get_health_summary": health,
        "log_finance": finance,
        "get_finance_summary": finance,
        "create_todo": schedule,
        "update_todo": schedule,
        "delete_todo": schedule,
        "get_todos": schedule,
        "create_habit": habit,
        "checkin_habit": habit,
        "get_habit_summary": habit,
        "create_diary": diary,
        "get_diary_summary": diary,
        "get_weather": weather,
        "get_weather_forecast": weather,
        "create_budget": budget_tools,
        "get_budget_status": budget_tools,
        "delete_budget": budget_tools,
        "update_user_location": settings_tools,
        "get_user_profile": settings_tools,
        "search_all": search_tools,
        "create_reminder": reminder_tools,
        "get_reminders": reminder_tools,
        "delete_reminder": reminder_tools,
        "get_overall_stats": stats_tools,
        "get_today_summary": stats_tools,
        "create_goal": goals_tools,
        "get_goals": goals_tools,
        "update_goal_progress": goals_tools,
        "delete_goal": goals_tools,
        "generate_weekly_report": report_tools,
        "generate_monthly_report": report_tools,
        "generate_insights": report_tools,
        "parse_quick_command": command_tools,
        "remember_memory": None,
        "recall_memory": None,
    }
    if name in ("remember_memory", "recall_memory"):
        if name == "remember_memory":
            return _do_remember_memory(arguments, db, user_id)
        else:
            return _do_recall_memory(arguments, db, user_id)
    if name not in ns:
        return {"error": f"未知工具: {name}"}
    return ns[name].execute(name, arguments, db, user_id)
