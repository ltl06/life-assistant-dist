"""Agent 路由 - 自主执行型 AI 生活助手"""
import os
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db, User, AgentMemory, AgentTask
from routers.auth import get_current_user

router = APIRouter(tags=["Agent"])


class AgentChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []


class AgentChatResponse(BaseModel):
    reply: str
    task_id: int
    steps: List[dict]
    status: str


class MemoryItem(BaseModel):
    key: str
    value: str


class MemoryWrite(BaseModel):
    key: str
    value: str


class TaskItem(BaseModel):
    id: int
    goal: str
    status: str
    result: Optional[str]
    created_at: datetime
    steps: List[dict]


def _api_config() -> dict:
    return {
        "api_key": os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY", ""),
        "base_url": os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com"),
        "model": os.getenv("OPENAI_MODEL", "deepseek-chat"),
    }


@router.post("/chat", response_model=AgentChatResponse)
def agent_chat(req: AgentChatRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from agent.core import run_agent
    cfg = _api_config()
    if not cfg["api_key"]:
        return AgentChatResponse(
            reply="AI 服务未配置，请在 .env 中设置 OPENAI_API_KEY 或 DEEPSEEK_API_KEY",
            task_id=0,
            steps=[],
            status="failed",
        )
    result = run_agent(current_user.id, req.message, db, req.history)
    return AgentChatResponse(
        reply=result["reply"],
        task_id=result["task_id"],
        steps=result["steps"],
        status=result["status"],
    )


@router.get("/tasks", response_model=List[TaskItem])
def get_tasks(limit: int = 20, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tasks = db.query(AgentTask).filter(
        AgentTask.user_id == current_user.id,
    ).order_by(AgentTask.created_at.desc()).limit(limit).all()
    return [
        TaskItem(
            id=t.id,
            goal=t.goal,
            status=t.status,
            result=t.result,
            created_at=t.created_at,
            steps=[],
        )
        for t in tasks
    ]


@router.get("/tasks/{task_id}", response_model=TaskItem)
def get_task(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    import json
    t = db.query(AgentTask).filter(
        AgentTask.id == task_id,
        AgentTask.user_id == current_user.id,
    ).first()
    if not t:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="任务不存在")
    steps = []
    if t.steps:
        try:
            steps = json.loads(t.steps)
        except Exception:
            pass
    return TaskItem(
        id=t.id, goal=t.goal, status=t.status, result=t.result,
        created_at=t.created_at, steps=steps,
    )


@router.get("/memory", response_model=List[MemoryItem])
def get_memory(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    mems = db.query(AgentMemory).filter(
        AgentMemory.user_id == current_user.id,
    ).order_by(AgentMemory.updated_at.desc()).all()
    return [MemoryItem(key=m.key, value=m.value) for m in mems]


@router.post("/memory")
def write_memory(req: MemoryWrite, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing = db.query(AgentMemory).filter(
        AgentMemory.user_id == current_user.id,
        AgentMemory.key == req.key,
    ).first()
    if existing:
        existing.value = req.value
        existing.updated_at = datetime.utcnow()
    else:
        mem = AgentMemory(user_id=current_user.id, key=req.key, value=req.value)
        db.add(mem)
    db.commit()
    return {"success": True, "key": req.key}


@router.delete("/memory/{key}")
def delete_memory(key: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db.query(AgentMemory).filter(
        AgentMemory.user_id == current_user.id,
        AgentMemory.key == key,
    ).delete(synchronize_session=False)
    db.commit()
    return {"success": True}
