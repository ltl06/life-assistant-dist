"""AI 助手路由"""
import os
from dotenv import load_dotenv
load_dotenv()
from typing import Optional, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db, User
from routers.auth import get_current_user

router = APIRouter()

class AIRequest(BaseModel):
    message: str
    context: Optional[str] = None

class AIResponse(BaseModel):
    reply: str
    suggestions: Optional[List[str]] = None

def call_ai_api(prompt: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return "AI 服务未配置。请在 .env 中设置 OPENAI_API_KEY 或 DEEPSEEK_API_KEY。"
    try:
        import httpx
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        resp = httpx.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json={"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 500},
            timeout=30.0,
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        else:
            return f"AI 服务返回错误: {resp.status_code} - {resp.text[:100]}"
    except Exception as e:
        return f"AI 服务调用失败: {str(e)}"

@router.post("/chat", response_model=AIResponse)
def ai_chat(req: AIRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    system_prompt = (
        "你是一个贴心、智能的生活小助手，名叫「小周」。"
        "你可以帮助用户：\n"
        "1. 回答健康问题（饮食、运动、睡眠建议）\n"
        "2. 财务规划（记账建议、预算建议）\n"
        "3. 时间管理（待办事项、日程规划）\n"
        "4. 情绪陪伴（倾听、安慰、鼓励）\n"
        "5. 日常问答（天气、新闻、实用信息）\n"
        "用温暖、口语化的方式回复，简短有力，偶尔用 emoji 增添活力。"
        "记住用户偏好，提供个性化建议。回复控制在 200 字以内。"
    )
    user_prompt = f"{system_prompt}\n\n用户：{req.message}"
    reply = call_ai_api(user_prompt)
    return AIResponse(
        reply=reply,
        suggestions=["帮我记账", "提醒我喝水", "分析我的健康数据", "规划明天的待办"],
    )
