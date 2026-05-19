"""效率工具路由"""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db, User, Todo, Habit, Reminder
from routers.auth import get_current_user

router = APIRouter()

class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    due_date: Optional[datetime] = None

class TodoOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    completed: bool
    priority: str
    due_date: Optional[datetime]
    class Config:
        from_attributes = True

class HabitCreate(BaseModel):
    name: str
    frequency: str
    target: int = 1

class HabitOut(BaseModel):
    id: int
    name: str
    frequency: str
    target: int
    current_streak: int
    class Config:
        from_attributes = True

class ReminderCreate(BaseModel):
    title: str
    message: Optional[str] = None
    remind_at: datetime

class ReminderOut(BaseModel):
    id: int
    title: str
    message: Optional[str]
    remind_at: datetime
    sent: bool
    class Config:
        from_attributes = True

@router.get("/todos", response_model=List[TodoOut])
def get_todos(completed: Optional[bool] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(Todo).filter(Todo.user_id == current_user.id)
    if completed is not None:
        q = q.filter(Todo.completed == completed)
    return q.order_by(Todo.created_at.desc()).all()

@router.post("/todos", response_model=TodoOut)
def create_todo(todo: TodoCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    t = Todo(user_id=current_user.id, title=todo.title, description=todo.description, priority=todo.priority, due_date=todo.due_date)
    db.add(t); db.commit(); db.refresh(t)
    return t

@router.patch("/todos/{todo_id}", response_model=TodoOut)
def update_todo(todo_id: int, completed: bool, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    t = db.query(Todo).filter(Todo.id == todo_id, Todo.user_id == current_user.id).first()
    if not t:
        return {"error": "未找到"}
    t.completed = completed
    db.commit(); db.refresh(t)
    return t

@router.delete("/todos/{todo_id}")
def delete_todo(todo_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    t = db.query(Todo).filter(Todo.id == todo_id, Todo.user_id == current_user.id).first()
    if t:
        db.delete(t); db.commit()
    return {"ok": True}

@router.get("/habits", response_model=List[HabitOut])
def get_habits(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Habit).filter(Habit.user_id == current_user.id).all()

@router.post("/habits", response_model=HabitOut)
def create_habit(habit: HabitCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    h = Habit(user_id=current_user.id, name=habit.name, frequency=habit.frequency, target=habit.target)
    db.add(h); db.commit(); db.refresh(h)
    return h

@router.post("/habits/{habit_id}/checkin")
def checkin_habit(habit_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    h = db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == current_user.id).first()
    if not h:
        return {"error": "未找到"}
    h.current_streak += 1
    db.commit()
    return {"streak": h.current_streak}

@router.get("/reminders", response_model=List[ReminderOut])
def get_reminders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Reminder).filter(Reminder.user_id == current_user.id, Reminder.sent == False).all()

@router.post("/reminders", response_model=ReminderOut)
def create_reminder(reminder: ReminderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = Reminder(user_id=current_user.id, title=reminder.title, message=reminder.message, remind_at=reminder.remind_at)
    db.add(r); db.commit(); db.refresh(r)
    return r

@router.delete("/reminders/{reminder_id}")
def delete_reminder(reminder_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = db.query(Reminder).filter(Reminder.id == reminder_id, Reminder.user_id == current_user.id).first()
    if r:
        db.delete(r); db.commit()
    return {"ok": True}
