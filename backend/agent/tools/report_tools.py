"""周期报告生成工具 - 自动生成周报/月报"""
from datetime import date, timedelta
import json

functions = [
    {
        "type": "function",
        "function": {
            "name": "generate_weekly_report",
            "description": "生成用户本周的详细生活报告，包含健康、财务、习惯、情绪等多维度数据，适合周末复盘。",
            "parameters": {
                "type": "object",
                "properties": {
                    "week_offset": {
                        "type": "integer",
                        "description": "周偏移量，0=本周，-1=上周，-2=上上周，默认0",
                        "default": 0,
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_monthly_report",
            "description": "生成用户本月的详细生活报告，包含健康、财务、习惯、情绪等所有模块的月度数据汇总与趋势分析。",
            "parameters": {
                "type": "object",
                "properties": {
                    "year_month": {
                        "type": "string",
                        "description": "月份，格式 YYYY-MM，如 2026-04。不填则默认本月。",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_insights",
            "description": "基于用户历史数据，生成个性化的智能洞察和建议。分析健康、财务、习惯等数据，发现规律和问题，给出可操作的建议。",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "分析天数，默认30天",
                        "default": 30,
                    },
                },
                "required": [],
            },
        },
    },
]


def execute(name: str, args: dict, db, user_id: int):
    if name == "generate_weekly_report":
        return _weekly_report(args, db, user_id)
    if name == "generate_monthly_report":
        return _monthly_report(args, db, user_id)
    if name == "generate_insights":
        return _insights(args, db, user_id)
    return {"error": f"未知工具: {name}"}


def _get_date_range(period="week", week_offset=0, year_month=None):
    today = date.today()
    if period == "week":
        days_since_monday = today.weekday()
        monday = today - timedelta(days=days_since_monday + week_offset * 7)
        sunday = monday + timedelta(days=6)
        return monday, sunday, f"第{monday.isocalendar()[1]}周"
    else:
        if year_month:
            y, m = map(int, year_month.split("-"))
        else:
            y, m = today.year, today.month
        start = date(y, m, 1)
        if m == 12:
            end = date(y + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(y, m + 1, 1) - timedelta(days=1)
        return start, end, f"{y}年{m}月"


def _weekly_report(args: dict, db, user_id: int):
    from database import HealthRecord, FinanceRecord, Diary, Todo, Habit, HabitCheckin

    start, end, label = _get_date_range("week", args.get("week_offset", 0))

    health = db.query(HealthRecord).filter(
        HealthRecord.user_id == user_id,
        HealthRecord.date >= start, HealthRecord.date <= end,
    ).all()
    finance = db.query(FinanceRecord).filter(
        FinanceRecord.user_id == user_id,
        FinanceRecord.date >= start, FinanceRecord.date <= end,
    ).all()
    diaries = db.query(Diary).filter(
        Diary.user_id == user_id,
        Diary.date >= start, Diary.date <= end,
    ).all()
    todos = db.query(Todo).filter(Todo.user_id == user_id).all()
    habits = db.query(Habit).filter(Habit.user_id == user_id).all()
    habit_ids = [h.id for h in habits]

    checkins = db.query(HabitCheckin).filter(
        HabitCheckin.user_id == user_id,
        HabitCheckin.date >= start, HabitCheckin.date <= end,
        HabitCheckin.habit_id.in_(habit_ids),
    ).all() if habit_ids else []

    # 健康
    steps = [r.steps for r in health if r.steps]
    sleeps = [r.sleep_hours for r in health if r.sleep_hours]
    moods_h = [r.mood for r in health if r.mood]
    avg_steps = round(sum(steps) / len(steps)) if steps else 0

    # 财务
    income = sum(r.amount for r in finance if r.type == "income")
    expense = sum(r.amount for r in finance if r.type == "expense")
    expense_days = sum(1 for r in finance if r.type == "expense")

    # 日记
    diary_count = len(diaries)
    moods_d = [d.mood for d in diaries if d.mood]
    top_mood = max(set(moods_d), key=moods_d.count) if moods_d else "未记录"

    # 待办
    todos_in_range = [t for t in todos if t.created_at and start <= t.created_at.date() <= end]
    completed_todos = sum(1 for t in todos_in_range if t.completed)
    todo_completion = round(completed_todos / len(todos_in_range) * 100) if todos_in_range else 0

    # 习惯
    habit_map = {h.id: h.name for h in habits}
    habit_stats = {}
    for h in habits:
        count = sum(1 for c in checkins if c.habit_id == h.id)
        habit_stats[h.name] = {"checked": count, "total": 7}

    # 生成周评价
    scores = []
    if avg_steps >= 6000:
        scores.append(("运动", "优秀", f"日均{avg_steps}步"))
    elif avg_steps > 0:
        scores.append(("运动", "一般", f"日均{avg_steps}步，建议增加活动量"))
    if sum(sleeps) / len(sleeps) >= 7 if sleeps else False:
        scores.append(("睡眠", "优秀", "睡眠充足"))
    elif sleeps:
        scores.append(("睡眠", "一般", f"平均睡眠{sum(sleeps)/len(sleeps):.1f}小时"))
    if expense_days <= 3:
        scores.append(("消费", "优秀", "消费节制"))
    elif expense > 0:
        scores.append(("消费", "一般", f"本周消费{expense:.0f}元"))
    if diary_count >= 5:
        scores.append(("日记", "优秀", f"记录{diary_count}篇"))
    elif diary_count > 0:
        scores.append(("日记", "一般", f"记录{diary_count}篇"))

    summary = {
        "period": label,
        "date_range": f"{start} ~ {end}",
        "health": {
            "days_recorded": len(health),
            "avg_steps": avg_steps,
            "avg_sleep": round(sum(sleeps) / len(sleeps), 1) if sleeps else None,
            "mood_distribution": {m: moods_h.count(m) for m in set(moods_h)} if moods_h else {},
        },
        "finance": {
            "income": round(income, 2),
            "expense": round(expense, 2),
            "balance": round(income - expense, 2),
        },
        "diary": {
            "count": diary_count,
            "top_mood": top_mood,
        },
        "todos": {
            "completed": completed_todos,
            "total": len(todos_in_range),
            "completion_rate": todo_completion,
        },
        "habits": habit_stats,
        "scores": scores,
    }

    # 生成文字报告
    report_lines = [
        f"📅 {label}生活报告（{start} ~ {end}）",
        "",
    ]
    if scores:
        report_lines.append("🏆 本周亮点：")
        for s in scores:
            report_lines.append(f"  • {s[0]}：{s[1]} - {s[2]}")
        report_lines.append("")

    report_lines.append("💪 健康数据：")
    report_lines.append(f"  记录天数：{len(health)}/7天")
    if steps:
        report_lines.append(f"  平均步数：{avg_steps}步/天")
    if sleeps:
        report_lines.append(f"  平均睡眠：{sum(seps := sleeps) / len(seps):.1f}小时")
    if moods_h:
        report_lines.append(f"  主要心情：{top_mood}")
    report_lines.append("")

    report_lines.append("💰 财务数据：")
    report_lines.append(f"  收入：{income:.0f}元 | 支出：{expense:.0f}元 | 结余：{income - expense:.0f}元")
    report_lines.append("")

    report_lines.append(f"📝 日记：{diary_count}篇")
    report_lines.append(f"✅ 待办完成：{completed_todos}/{len(todos_in_range)} ({todo_completion}%)")
    report_lines.append(f"🌱 习惯打卡：{len(checkins)}次")

    summary["report_text"] = "\n".join(report_lines)
    return summary


def _monthly_report(args: dict, db, user_id: int):
    from database import HealthRecord, FinanceRecord, Diary, Todo, Habit, HabitCheckin

    start, end, label = _get_date_range("month", year_month=args.get("year_month"))

    health = db.query(HealthRecord).filter(
        HealthRecord.user_id == user_id,
        HealthRecord.date >= start, HealthRecord.date <= end,
    ).all()
    finance = db.query(FinanceRecord).filter(
        FinanceRecord.user_id == user_id,
        FinanceRecord.date >= start, FinanceRecord.date <= end,
    ).all()
    diaries = db.query(Diary).filter(
        Diary.user_id == user_id,
        Diary.date >= start, Diary.date <= end,
    ).all()
    todos = db.query(Todo).filter(Todo.user_id == user_id).all()
    habits = db.query(Habit).filter(Habit.user_id == user_id).all()
    habit_ids = [h.id for h in habits]

    checkins = db.query(HabitCheckin).filter(
        HabitCheckin.user_id == user_id,
        HabitCheckin.date >= start, HabitCheckin.date <= end,
        HabitCheckin.habit_id.in_(habit_ids),
    ).all() if habit_ids else []

    days_in_month = (end - start).days + 1

    steps = [r.steps for r in health if r.steps]
    sleeps = [r.sleep_hours for r in health if r.sleep_hours]
    weights = [r.weight for r in health if r.weight]
    moods_h = [r.mood for r in health if r.mood]

    income = sum(r.amount for r in finance if r.type == "income")
    expense = sum(r.amount for r in finance if r.type == "expense")
    by_cat = {}
    for r in finance:
        if r.type == "expense":
            by_cat[r.category] = by_cat.get(r.category, 0) + r.amount

    diary_count = len(diaries)
    moods_d = [d.mood for d in diaries if d.mood]

    habit_stats = {}
    for h in habits:
        count = sum(1 for c in checkins if c.habit_id == h.id)
        rate = round(count / days_in_month * 100)
        habit_stats[h.name] = {"checkins": count, "days": days_in_month, "rate": rate}

    # 月度综合评价
    total_score = 0
    factors = []
    if steps:
        avg_steps = sum(steps) / len(steps)
        s_score = min(100, int(avg_steps / 100))
        total_score += s_score
        factors.append(("运动", s_score, f"日均{avg_steps:.0f}步"))
    if sleeps:
        avg_sleep = sum(sleeps) / len(sleeps)
        sl_score = 100 if avg_sleep >= 7 else int(avg_sleep / 7 * 100)
        total_score += sl_score
        factors.append(("睡眠", sl_score, f"均{avg_sleep:.1f}h"))
    if weights:
        total_score += 80
        factors.append(("体重", 80, f"记录{len(weights)}次"))
    if income > 0:
        save_rate = int((income - expense) / income * 100)
        total_score += max(0, min(100, save_rate + 50))
        factors.append(("储蓄", max(0, min(100, save_rate + 50)), f"储蓄率{save_rate}%"))
    if diary_count >= 20:
        total_score += 90
        factors.append(("日记", 90, f"{diary_count}篇"))
    elif diary_count > 0:
        total_score += 60
        factors.append(("日记", 60, f"{diary_count}篇"))

    avg_score = round(total_score / max(len(factors), 1), 1)

    report_text = f"""📊 {label}月度生活报告（{start} ~ {end}）

🏅 综合评分：{avg_score}分

💪 健康：
  记录天数：{len(health)}/{days_in_month}天
  平均步数：{round(sum(steps)/len(steps)) if steps else 0}步/天
  平均睡眠：{round(sum(sleeps)/len(sleeps), 1) if sleeps else '--'}小时
  体重记录：{len(weights)}次
  心情分布：{dict({m: moods_h.count(m) for m in set(moods_h)}) if moods_h else '无'}

💰 财务：
  收入：{income:.0f}元 | 支出：{expense:.0f}元 | 结余：{income - expense:.0f}元
  主要支出：{max(by_cat, key=by_cat.get) if by_cat else '无'}（{max(by_cat.values()) if by_cat else 0:.0f}元）

📝 日记：{diary_count}篇
  心情趋势：{dict({m: moods_d.count(m) for m in set(moods_d)}) if moods_d else '无'}

🌱 习惯追踪："""
    for name, stat in habit_stats.items():
        report_text += f"\n  {name}：打卡{stat['checkins']}次（{stat['rate']}%）"

    report_text += f"\n\n✅ 总体评价："
    for f_name, score, detail in factors:
        emoji = "🌟" if score >= 80 else "⭐" if score >= 60 else "📌"
        report_text += f"\n  {emoji} {f_name} {score}分 - {detail}"

    return {
        "period": label,
        "date_range": f"{start} ~ {end}",
        "overall_score": avg_score,
        "factors": factors,
        "health": {
            "days_recorded": len(health),
            "total_days": days_in_month,
            "avg_steps": round(sum(steps) / len(steps)) if steps else 0,
            "avg_sleep": round(sum(sleeps) / len(seps := sleeps), 1) if sleeps else None,
            "mood_distribution": {m: moods_h.count(m) for m in set(moods_h)} if moods_h else {},
        },
        "finance": {
            "income": round(income, 2),
            "expense": round(expense, 2),
            "balance": round(income - expense, 2),
            "expense_by_category": {k: round(v, 2) for k, v in sorted(by_cat.items(), key=lambda x: -x[1])},
        },
        "diary": {"count": diary_count},
        "habits": habit_stats,
        "report_text": report_text,
    }


def _insights(args: dict, db, user_id: int):
    from database import HealthRecord, FinanceRecord, Diary, Habit, HabitCheckin, Todo

    days = args.get("days", 30)
    start = date.today() - timedelta(days=days)

    health = db.query(HealthRecord).filter(
        HealthRecord.user_id == user_id, HealthRecord.date >= start
    ).all()
    finance = db.query(FinanceRecord).filter(
        FinanceRecord.user_id == user_id, FinanceRecord.date >= start
    ).all()
    diaries = db.query(Diary).filter(
        Diary.user_id == user_id, Diary.date >= start
    ).all()
    habits = db.query(Habit).filter(Habit.user_id == user_id).all()
    todos = db.query(Todo).filter(Todo.user_id == user_id).all()
    habit_ids = [h.id for h in habits]
    checkins = db.query(HabitCheckin).filter(
        HabitCheckin.user_id == user_id, HabitCheckin.date >= start,
        HabitCheckin.habit_id.in_(habit_ids),
    ).all() if habit_ids else []

    insights = []

    # 健康洞察
    if len(health) < days * 0.5:
        insights.append({
            "category": "健康",
            "type": "warning",
            "icon": "⚠️",
            "title": "健康记录不够规律",
            "detail": f"过去{days}天只记录了{len(health)}天，建议养成每天记录的习惯，这样小周才能更好地分析趋势。",
            "suggestion": "可以在每天睡前花1分钟记录当天的健康数据",
        })

    sleeps = [r.sleep_hours for r in health if r.sleep_hours]
    if sleeps:
        avg_sleep = sum(sleeps) / len(sleeps)
        if avg_sleep < 6:
            insights.append({
                "category": "健康", "type": "warning", "icon": "😴",
                "title": "睡眠时长偏少",
                "detail": f"平均每天只睡{avg_sleep:.1f}小时，低于推荐的7-9小时。",
                "suggestion": "建议提前30分钟上床，形成规律作息。",
            })
        elif avg_sleep >= 7:
            insights.append({
                "category": "健康", "type": "positive", "icon": "😊",
                "title": "睡眠质量良好",
                "detail": f"平均睡眠{avg_sleep:.1f}小时，符合健康标准。",
                "suggestion": "继续保持！",
            })

    steps = [r.steps for r in health if r.steps]
    if steps:
        avg_steps = sum(steps) / len(steps)
        if avg_steps < 5000:
            insights.append({
                "category": "健康", "type": "warning", "icon": "🏃",
                "title": "运动量偏低",
                "detail": f"日均{avg_steps:.0f}步，低于推荐的6000-10000步。",
                "suggestion": "每天多走15-20分钟，或设置步数提醒。",
            })

    # 财务洞察
    expense = [r for r in finance if r.type == "expense"]
    if expense:
        by_cat = {}
        for r in expense:
            by_cat[r.category] = by_cat.get(r.category, 0) + r.amount
        if by_cat:
            top_cat = max(by_cat, key=by_cat.get)
            top_amt = by_cat[top_cat]
            if top_amt > sum(by_cat.values()) * 0.4:
                insights.append({
                    "category": "财务", "type": "warning", "icon": "💸",
                    "title": f"{top_cat}支出占比较高",
                    "detail": f"过去{days}天，{top_cat}支出{top_amt:.0f}元，占总支出{int(top_amt/sum(by_cat.values())*100)}%。",
                    "suggestion": f"可以关注一下{top_cat}消费，看看有没有节省空间。",
                })

    income = sum(r.amount for r in finance if r.type == "income")
    total_exp = sum(r.amount for r in expense)
    if income > 0 and total_exp > income:
        insights.append({
            "category": "财务", "type": "danger", "icon": "🚨",
            "title": "本月入不敷出",
            "detail": f"收入{income:.0f}元，支出{total_exp:.0f}元，超支{total_exp - income:.0f}元。",
            "suggestion": "建议使用预算功能设置支出上限，避免超支。",
        })

    # 习惯洞察
    for h in habits:
        h_checkins = [c for c in checkins if c.habit_id == h.id]
        if len(h_checkins) >= days * 0.8:
            insights.append({
                "category": "习惯", "type": "positive", "icon": "🎉",
                "title": f"「{h.name}」坚持得很好",
                "detail": f"过去{days}天打卡{len(h_checkins)}次，达成率{int(len(h_checkins)/days*100)}%。",
                "suggestion": "继续保持！",
            })
        elif len(h_checkins) < days * 0.3 and len(h_checkins) > 0:
            insights.append({
                "category": "习惯", "type": "warning", "icon": "📉",
                "title": f"「{h.name}」需要加强",
                "detail": f"过去{days}天只打卡{len(h_checkins)}次。",
                "suggestion": "可以降低目标频率，或者让小周每天提醒你。",
            })

    # 日记洞察
    if len(diaries) >= 20:
        insights.append({
            "category": "日记", "type": "positive", "icon": "✍️",
            "title": "日记记录很棒",
            "detail": f"过去{days}天写了{len(diaries)}篇日记，写作习惯良好。",
            "suggestion": "坚持记录，复盘会更有收获。",
        })
    elif len(diaries) == 0:
        insights.append({
            "category": "日记", "type": "info", "icon": "📝",
            "title": "还没有写日记",
            "detail": f"过去{days}天没有日记记录。",
            "suggestion": "可以尝试每天写几句话，记录情绪和感悟。",
        })

    # 待办洞察
    if todos:
        active = [t for t in todos if not t.completed]
        overdue = [t for t in active if t.due_date and t.due_date.date() < date.today()]
        if overdue:
            insights.append({
                "category": "待办", "type": "warning", "icon": "📋",
                "title": f"有{len(overdue)}个待办已过期",
                "detail": "这些待办已过截止日期仍未完成。",
                "suggestion": "检查一下这些任务，决定是删除还是重新设置截止日期。",
            })

    if not insights:
        insights.append({
            "category": "总体", "type": "info", "icon": "🌟",
            "title": "数据暂时不足以生成个性化洞察",
            "detail": "多记录几天数据后，小周可以给出更有针对性的建议。",
            "suggestion": "建议每天记录健康、记账、写日记，小周会越了解你。",
        })

    return {
        "period_days": days,
        "date_range": f"{start} 至 {date.today()}",
        "total_insights": len(insights),
        "insights": insights,
        "summary": f"共生成 {len(insights)} 条洞察，其中 {sum(1 for i in insights if i['type'] == 'positive')} 条积极、{sum(1 for i in insights if i['type'] == 'warning')} 条待改进。",
    }
