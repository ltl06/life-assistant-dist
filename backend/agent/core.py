"""Agent 核心模块 - 基于 Function Calling 的自主执行循环"""
import json
import os
import httpx
from datetime import datetime
from database import AgentMemory, AgentTask, User

MAX_ITERATIONS = 10
TOOL_CALL_MARKER = "[TOOL_CALL]"


def get_system_prompt() -> str:
    return """你是一个自主执行型生活管理 Agent，名叫「小周」。

当用户给你一个目标时，你需要：
1. 理解目标，拆解为可执行的步骤
2. 调用工具逐步执行（每次调用 1-2 个工具）
3. 在执行过程中告诉用户你正在做什么
4. 主动记住用户的偏好和关键信息（调用 remember_memory）
5. 任务完成后给出总结和后续建议

你有以下工具可用，请仔细了解每个工具的用途和参数：
- log_health: 记录运动/睡眠/体重/心情
- get_health_summary: 查看健康数据趋势
- log_finance: 记录收支流水
- get_finance_summary: 查看财务汇总
- create_todo / update_todo / delete_todo / get_todos: 待办事项管理
- create_habit / checkin_habit / get_habit_summary: 习惯追踪
- create_diary / get_diary_summary: 日记管理
- get_weather: 查询当前天气和穿衣建议（需要城市名）
- get_weather_forecast: 查询未来3天天气预报
- create_budget / get_budget_status / delete_budget: 月度预算管理
- update_user_location / get_user_profile: 用户设置
- search_all: 全局搜索，跨模块找记录
- create_reminder / get_reminders / delete_reminder: 提醒管理
- get_overall_stats: 一键获取所有模块的30天统计数据
- get_today_summary: 今日数据快速汇总
- create_goal / get_goals / update_goal_progress / delete_goal: 长期目标追踪与拆解
- generate_weekly_report: 生成本周生活报告
- generate_monthly_report: 生成月度生活报告
- generate_insights: 基于历史数据生成智能洞察和建议
- parse_quick_command: 自然语言一键录入（记账/健康/日记/待办）
- remember_memory / recall_memory: 记忆管理

**重要规则**：
- 如果用户只是闲聊，直接回复，不需要调用任何工具
- 如果用户给了一个任务/目标，主动规划并调用工具执行
- 不要在一个回合内调用超过 2 个工具
- 记录重要信息后用 remember_memory 保存，这样下次对话可以记住
- 调用工具后，等待结果，再决定下一步
- 回复要温暖、口语化，偶尔用 emoji，控制在 200 字以内
- 用户说"帮我查一下"、"搜索"、"找找"时，优先用 search_all
- 用户想了解今天的整体情况时，用 get_today_summary
- 用户想看整体趋势或统计数据时，用 get_overall_stats
- 用户设置提醒时间时，用 create_reminder（格式：YYYY-MM-DD HH:MM）
- 用户说"记账"或"记支出/收入"时，先用 parse_quick_command 解析自然语言
- 用户说"生成报告"、"周报"、"月报"时，用 generate_weekly_report 或 generate_monthly_report
- 用户说"给我建议"、"分析一下"、"洞察"时，用 generate_insights
- 用户设定长期目标时，用 create_goal（会自动生成里程碑）"""


def get_memory_context(db, user_id: int) -> str:
    memories = db.query(AgentMemory).filter(AgentMemory.user_id == user_id).all()
    if not memories:
        return ""
    lines = ["【已记住的用户信息】"]
    for m in memories:
        lines.append(f"- {m.key}: {m.value}")
    return "\n".join(lines)


def call_llm(messages: list, tools: list) -> dict:
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    if deepseek_key and deepseek_key not in ("", "your-deepseek-api-key-here"):
        api_key = deepseek_key
        base_url = "https://api.deepseek.com"
        model = "deepseek-chat"
    elif openai_key and openai_key not in ("", "your-openai-api-key-here"):
        api_key = openai_key
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    else:
        return {"error": "AI 服务未配置，请检查 .env 中的 DEEPSEEK_API_KEY"}

    try:
        import httpx
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        resp = httpx.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json={
                "model": model,
                "messages": messages,
                "tools": tools,
                "max_tokens": 800,
            },
            timeout=60.0,
        )
        if resp.status_code == 200:
            return resp.json()
        else:
            return {"error": f"AI 返回错误 {resp.status_code}: {resp.text[:200]}"}
    except Exception as e:
        return {"error": f"调用 AI 失败: {str(e)}"}


def run_agent(user_id: int, user_message: str, db, conversation_history: list) -> dict:
    from agent.tools import execute_tool, ALL_TOOLS

    task = AgentTask(user_id=user_id, goal=user_message, steps="[]", status="running")
    db.add(task)
    db.commit()
    db.refresh(task)

    memory_context = get_memory_context(db, user_id)

    system_content = get_system_prompt()
    if memory_context:
        system_content += "\n\n" + memory_context

    messages = [
        {"role": "system", "content": system_content},
    ]
    for entry in conversation_history[-10:]:
        role = "user" if entry.get("role") == "user" else "assistant"
        content = entry.get("text") or entry.get("content", "")
        messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_message})

    steps = []
    step_count = 0
    final_reply = ""

    while step_count < MAX_ITERATIONS:
        step_count += 1
        result = call_llm(messages, ALL_TOOLS)

        if "error" in result:
            final_reply = result["error"]
            break

        choices = result.get("choices", [])
        if not choices:
            final_reply = "AI 返回格式异常"
            break

        choice = choices[0]
        msg = choice.get("message", {})

        assistant_text = msg.get("content") or ""
        tool_calls = msg.get("tool_calls", [])
        if not tool_calls:
            final_reply = assistant_text or "小周暂时没有回复，稍等一下再试试~"
            break

        # 先添加 assistant 消息（包含 tool_calls），再添加 tool 结果
        messages.append({"role": "assistant", "content": assistant_text, "tool_calls": tool_calls})

        for tc in tool_calls:
            fn = tc.get("function", {})
            tool_name = fn.get("name")
            raw_args = fn.get("arguments", "{}")

            if isinstance(raw_args, str):
                try:
                    args = json.loads(raw_args)
                except Exception:
                    args = {}
            else:
                args = raw_args

            if tool_name == "remember_memory":
                _do_remember_memory(args, db, user_id)
                tool_result = {"success": True, "message": f"已记住：{args.get('key', '')}"}
            elif tool_name == "recall_memory":
                tool_result = _do_recall_memory(args, db, user_id)
            else:
                tool_result = execute_tool(tool_name, args, db, user_id)

            result_str = json.dumps(tool_result, ensure_ascii=False)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.get("id", ""),
                "name": tool_name,
                "content": result_str,
            })
            steps.append({
                "step": step_count,
                "tool": tool_name,
                "args": args,
                "result": tool_result,
            })

        # 限制每轮最多 2 个 tool call
        if len(tool_calls) > 2:
            messages.append({
                "role": "assistant",
                "content": "（本轮工具调用过多，已自动截断。继续执行最重要的 2 个步骤。）"
            })

    # 保存任务结果
    task.status = "done" if steps else "done"
    task.steps = json.dumps(steps, ensure_ascii=False)
    task.result = final_reply
    db.commit()

    return {
        "reply": final_reply,
        "task_id": task.id,
        "steps": steps,
        "status": task.status,
    }


def _do_remember_memory(args: dict, db, user_id: int):
    key = args.get("key", "").strip()
    value = args.get("value", "").strip()
    if not key or not value:
        return {"success": False, "message": "key 和 value 均不能为空"}

    existing = db.query(AgentMemory).filter(
        AgentMemory.user_id == user_id,
        AgentMemory.key == key,
    ).first()
    if existing:
        existing.value = value
        existing.updated_at = datetime.utcnow()
    else:
        mem = AgentMemory(user_id=user_id, key=key, value=value)
        db.add(mem)
    db.commit()
    return {"success": True, "message": f"已记住：{key}"}


def _do_recall_memory(args: dict, db, user_id: int):
    key = args.get("key", "").strip()
    if key:
        mem = db.query(AgentMemory).filter(
            AgentMemory.user_id == user_id,
            AgentMemory.key == key,
        ).first()
        if mem:
            return {"key": mem.key, "value": mem.value}
        return {"key": key, "value": None, "message": "没有找到相关信息"}
    all_mem = db.query(AgentMemory).filter(AgentMemory.user_id == user_id).all()
    return {
        "memories": [{"key": m.key, "value": m.value} for m in all_mem],
    }


# 补充两个 memory 工具到 ALL_TOOLS（在 tools/__init__ 中注册）
def get_memory_tools():
    return [
        {
            "type": "function",
            "function": {
                "name": "remember_memory",
                "description": "主动记住用户的长期偏好、目标或重要信息，下次对话时可以 recalled。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "key": {"type": "string", "description": "记忆的键名（如：体重目标、健康偏好、理财计划）"},
                        "value": {"type": "string", "description": "要记住的内容"},
                    },
                    "required": ["key", "value"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "recall_memory",
                "description": "查询已记住的用户信息。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "key": {"type": "string", "description": "要查询的键名（不填则返回全部记忆）"},
                    },
                    "required": [],
                },
            },
        },
    ]
