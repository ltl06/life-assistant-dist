"""快捷指令解析工具 - 自然语言一键录入"""
from datetime import date, datetime, timedelta
import re

functions = [
    {
        "type": "function",
        "function": {
            "name": "parse_quick_command",
            "description": "解析自然语言快捷指令，一句话完成健康记录、记账、写日记、创建待办等多种操作。支持：记账（支出/收入）、健康记录（步数/睡眠/体重/心情）、日记、待办等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "用户的自然语言指令，如：记账午餐35元、今天跑了5公里、记一下今天心情不错",
                    },
                },
                "required": ["text"],
            },
        },
    },
]


def execute(name: str, args: dict, db, user_id: int):
    if name == "parse_quick_command":
        return _parse(args["text"], db, user_id)
    return {"error": f"未知工具: {name}"}


def _parse(text: str, db, user_id: int):
    from database import HealthRecord, FinanceRecord, Diary, Todo

    text = text.strip()
    results = []
    original = text

    # 记账相关
    finance_result = _parse_finance(text, db, user_id)
    if finance_result:
        results.append(finance_result)

    # 健康记录
    health_result = _parse_health(text, db, user_id)
    if health_result:
        results.append(health_result)

    # 日记
    diary_result = _parse_diary(text, db, user_id)
    if diary_result:
        results.append(diary_result)

    # 待办
    todo_result = _parse_todo(text, db, user_id)
    if todo_result:
        results.append(todo_result)

    if not results:
        return {
            "success": False,
            "message": "小周没能理解这条指令，你可以试试：\n- '记账 午餐 35元'\n- '今天跑了5000步'\n- '记录一下今天心情很好'\n- '帮我创建待办：明天下午开会'",
            "parsed": [],
        }

    summary = f"已处理 {len(results)} 项记录：\n" + "\n".join(f"✅ {r['message']}" for r in results)
    return {
        "success": True,
        "message": summary,
        "parsed": results,
    }


def _parse_finance(text: str, db, user_id: int):
    from database import FinanceRecord

    # 收入/支出关键词
    is_income = any(k in text for k in ["收入", "收到", "到账", "赚了", "发工资", "奖金"])
    is_expense = any(k in text for k in ["支出", "花了", "消费", "买", "记账", "花了"])

    if not (is_income or is_expense):
        # 纯数字+元 模式
        amount_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:元|块)', text)
        if amount_match:
            is_expense = True
        else:
            return None

    amount = None
    category = "其他"

    amount_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:元|块)', text)
    if amount_match:
        amount = float(amount_match.group(1))
    else:
        numbers = re.findall(r'\d+(?:\.\d+)?', text)
        if numbers:
            amount = float(numbers[-1])

    if not amount:
        return None

    # 分类识别
    if is_income:
        if "工资" in text or "发工资" in text:
            category = "工资"
        elif "奖金" in text:
            category = "奖金"
        elif "兼职" in text:
            category = "兼职"
        elif "投资" in text:
            category = "投资收益"
        else:
            category = "其他收入"
    else:
        if any(k in text for k in ["早餐", "午餐", "晚餐", "外卖", "吃饭", "餐饮", "食堂", "饭店", "下馆子"]):
            category = "餐饮"
        elif any(k in text for k in ["打车", "地铁", "公交", "交通", "开车", "停车", "油费", "高铁", "火车", "飞机"]):
            category = "交通"
        elif any(k in text for k in ["衣服", "鞋", "包", "购物", "网购", "淘宝", "京东"]):
            category = "购物"
        elif any(k in text for k in ["房租", "房贷", "水电", "物业"]):
            category = "居住"
        elif any(k in text for k in ["药", "医院", "挂号", "医疗", "看病"]):
            category = "医疗"
        elif any(k in text for k in ["学费", "培训", "书", "课程", "教育", "学习"]):
            category = "教育"
        elif any(k in text for k in ["电影", "游戏", "娱乐", "唱K", "旅游", "健身"]):
            category = "娱乐"
        elif any(k in text for k in ["话费", "流量", "宽带", "通讯"]):
            category = "通讯"
        elif any(k in text for k in ["护肤品", "化妆品", "美容", "理发", "服装"]):
            category = "服装"
        else:
            category = "其他"

    rec = FinanceRecord(
        user_id=user_id,
        type="income" if is_income else "expense",
        amount=amount,
        category=category,
        description=text,
        date=date.today(),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    action = "记收入" if is_income else "记支出"
    return {
        "type": "finance",
        "action": action,
        "message": f"{action}：{amount}元 [{category}]",
        "record_id": rec.id,
    }


def _parse_health(text: str, db, user_id: int):
    from database import HealthRecord

    steps = None
    sleep = None
    weight = None
    mood = None

    # 步数
    step_patterns = [
        (r'(\d+(?:\.\d+)?)\s*(?:万)?步', lambda m: int(float(m.group(1)) * 10000) if '万' in m.group(0) else int(m.group(1))),
        (r'跑了\s*(\d+(?:\.\d+)?)\s*(?:公里|km)', lambda m: int(float(m.group(1)) * 1300)),
        (r'走了\s*(\d+(?:\.\d+)?)\s*(?:公里|km)', lambda m: int(float(m.group(1)) * 1000)),
        (r'步行\s*(\d+(?:\.\d+)?)\s*(?:公里|km)', lambda m: int(float(m.group(1)) * 1000)),
    ]
    for pattern, converter in step_patterns:
        m = re.search(pattern, text)
        if m:
            steps = converter(m)
            break

    # 睡眠
    sleep_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:个?小?时?|h|小时)', text)
    if sleep_match and any(k in text for k in ["睡", "睡眠", "休息"]):
        sleep = float(sleep_match.group(1))
        if sleep > 24:
            sleep = sleep / 60

    # 体重
    weight_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:kg|公斤|斤)', text)
    if weight_match:
        weight = float(weight_match.group(1))
        if "斤" in weight_match.group(0):
            weight = weight / 2

    # 心情
    mood_map = {
        "开心": ["开心", "高兴", "快乐", "愉快", "不错", "棒", "好开心", "超开心", "很快乐"],
        "兴奋": ["兴奋", "激动", "太棒了", "超激动"],
        "平静": ["平静", "淡定", "平和", "放松", "休闲"],
        "一般": ["一般", "普通", "平常"],
        "低落": ["低落", "难过", "伤心", "郁闷"],
        "焦虑": ["焦虑", "担心", "紧张", "压力", "焦虑"],
        "疲惫": ["疲惫", "累", "疲倦", "困", "没精神"],
    }
    for mood_name, keywords in mood_map.items():
        if any(k in text for k in keywords):
            mood = mood_name
            break

    if not any([steps, sleep, weight, mood]):
        return None

    existing = db.query(HealthRecord).filter(
        HealthRecord.user_id == user_id,
        HealthRecord.date == date.today(),
    ).first()

    if existing:
        changed = []
        if steps is not None:
            existing.steps = steps
            changed.append(f"步数→{steps}")
        if sleep is not None:
            existing.sleep_hours = sleep
            changed.append(f"睡眠→{sleep}h")
        if weight is not None:
            existing.weight = weight
            changed.append(f"体重→{weight}kg")
        if mood is not None:
            existing.mood = mood
            changed.append(f"心情→{mood}")
        db.commit()
        return {
            "type": "health",
            "action": "更新健康记录",
            "message": f"今日健康已更新：{', '.join(changed)}",
            "record_id": existing.id,
        }

    rec = HealthRecord(
        user_id=user_id,
        date=date.today(),
        steps=steps or 0,
        sleep_hours=sleep,
        weight=weight,
        mood=mood,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    parts = []
    if steps:
        parts.append(f"步数={steps}")
    if sleep:
        parts.append(f"睡眠={sleep}h")
    if weight:
        parts.append(f"体重={weight}kg")
    if mood:
        parts.append(f"心情={mood}")

    return {
        "type": "health",
        "action": "记录健康数据",
        "message": f"已记录今日健康：{', '.join(parts)}",
        "record_id": rec.id,
    }


def _parse_diary(text: str, db, user_id: int):
    from database import Diary

    keywords = ["写日记", "写篇日记", "记日记", "今天", "心情", "日记", "感悟", "想法", "感觉", "觉得", "今日"]
    if not any(k in text for k in keywords):
        return None

    mood = None
    mood_map = {
        "开心": ["开心", "高兴", "快乐", "愉快", "不错", "好开心"],
        "兴奋": ["兴奋", "激动", "太棒了"],
        "平静": ["平静", "淡定", "平和", "放松"],
        "一般": ["一般", "普通", "平常"],
        "低落": ["低落", "难过", "伤心", "郁闷"],
        "焦虑": ["焦虑", "担心", "紧张"],
        "疲惫": ["疲惫", "累", "疲倦", "困"],
    }
    for mood_name, keywords_list in mood_map.items():
        if any(k in text for k in keywords_list):
            mood = mood_name
            break

    title = text[:30]
    rec = Diary(
        user_id=user_id,
        title=title,
        content=text,
        mood=mood,
        date=date.today(),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    return {
        "type": "diary",
        "action": "写日记",
        "message": f"已保存日记「{title[:20]}...」心情：{mood or '未标注'}",
        "record_id": rec.id,
    }


def _parse_todo(text: str, db, user_id: int):
    from database import Todo

    keywords = ["待办", "todo", "任务", "要做", "记得", "提醒我", "帮我", "创建"]
    if not any(k in text for k in keywords):
        return None

    title = text
    for prefix in ["待办", "todo", "任务", "要做", "记得", "提醒我", "帮我", "创建", "一下", "一个"]:
        title = re.sub(rf'^{re.escape(prefix)}[：:：]?\s*', '', title).strip()

    due_date = None
    due_match = re.search(r'(明天|后天|大后天|今天|下下周|第(\d+)周)', text)
    if due_match:
        today = date.today()
        kw = due_match.group(1)
        if "明天" in kw:
            due_date = today + timedelta(days=1)
        elif "后天" in kw:
            due_date = today + timedelta(days=2)
        elif "大后天" in kw:
            due_date = today + timedelta(days=3)
        elif "今天" in kw:
            due_date = today

    priority = "medium"
    if any(k in text for k in ["紧急", "重要", "必须", "马上", "立即"]):
        priority = "high"
    elif any(k in text for k in ["有空", "不急", "可以", "尽量"]):
        priority = "low"

    t = Todo(
        user_id=user_id,
        title=title[:100],
        priority=priority,
        due_date=datetime.combine(due_date, datetime.min.time()) if due_date else None,
    )
    db.add(t)
    db.commit()
    db.refresh(t)

    due_str = f"截止{due_date}" if due_date else ""
    return {
        "type": "todo",
        "action": "创建待办",
        "message": f"已创建待办「{title[:30]}」{due_str}（{priority}优先级）",
        "record_id": t.id,
    }
