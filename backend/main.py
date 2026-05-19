"""应用入口"""
import os
from dotenv import load_dotenv
load_dotenv()
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import (
    auth, health, finance, productivity, ai_assistant,
    weather, diary, budget, export, habit_tracker, quick_add, agent,
)
from database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _migrate_db(engine)
    yield

def _migrate_db(engine):
    from sqlalchemy import text
    with engine.connect() as conn:
        existing = set(r[0] for r in conn.execute(text("PRAGMA table_info(users)")).fetchall())
        if 'location' not in existing:
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN location VARCHAR"))
                conn.commit()
            except Exception:
                conn.rollback()
        existing_tables = set(r[0] for r in conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall())
        for table_sql in [
            ("diaries", "CREATE TABLE diaries (id INTEGER PRIMARY KEY, user_id INTEGER, date DATE, title VARCHAR, content TEXT, mood VARCHAR, tags VARCHAR, created_at DATETIME, updated_at DATETIME, FOREIGN KEY(user_id) REFERENCES users(id))"),
            ("budgets", "CREATE TABLE budgets (id INTEGER PRIMARY KEY, user_id INTEGER, year_month VARCHAR, category VARCHAR, budget_amount FLOAT, created_at DATETIME, FOREIGN KEY(user_id) REFERENCES users(id))"),
            ("habits", "CREATE TABLE habits (id INTEGER PRIMARY KEY, user_id INTEGER, name VARCHAR, frequency VARCHAR, target INTEGER, current_streak INTEGER, created_at DATETIME, FOREIGN KEY(user_id) REFERENCES users(id))"),
            ("habit_checkins", "CREATE TABLE habit_checkins (id INTEGER PRIMARY KEY, user_id INTEGER, habit_id INTEGER, date DATE, created_at DATETIME, FOREIGN KEY(user_id) REFERENCES users(id), FOREIGN KEY(habit_id) REFERENCES habits(id))"),
            ("agent_memory", "CREATE TABLE agent_memory (id INTEGER PRIMARY KEY, user_id INTEGER, key VARCHAR, value TEXT, created_at DATETIME, updated_at DATETIME, FOREIGN KEY(user_id) REFERENCES users(id))"),
            ("agent_tasks", "CREATE TABLE agent_tasks (id INTEGER PRIMARY KEY, user_id INTEGER, goal TEXT, steps TEXT, status VARCHAR DEFAULT 'pending', result TEXT, created_at DATETIME, updated_at DATETIME, FOREIGN KEY(user_id) REFERENCES users(id))"),
            ("reminders", "CREATE TABLE reminders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, title VARCHAR NOT NULL, remind_at DATETIME NOT NULL, note TEXT, triggered INTEGER DEFAULT 0, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)"),
            ("goals", "CREATE TABLE goals (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, title VARCHAR NOT NULL, description TEXT, category VARCHAR, target_date DATE, progress INTEGER DEFAULT 0, status VARCHAR DEFAULT 'active', milestones TEXT, notes TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME)"),
        ]:
            if table_sql[0] not in existing_tables:
                try:
                    conn.execute(text(table_sql[1]))
                    conn.commit()
                except Exception:
                    conn.rollback()

app = FastAPI(
    title="生活小助手 API",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(health.router, prefix="/api/health", tags=["健康"])
app.include_router(finance.router, prefix="/api/finance", tags=["财务"])
app.include_router(productivity.router, prefix="/api/productivity", tags=["效率"])
app.include_router(ai_assistant.router, prefix="/api/ai", tags=["AI助手"])
app.include_router(weather.router, prefix="/api/weather", tags=["天气"])
app.include_router(diary.router, prefix="/api/diary", tags=["日记"])
app.include_router(budget.router, prefix="/api/budget", tags=["预算"])
app.include_router(export.router, prefix="/api/export", tags=["导出"])
app.include_router(habit_tracker.router, prefix="/api/habits", tags=["习惯追踪"])
app.include_router(quick_add.router, prefix="/api/quick", tags=["快捷记录"])
app.include_router(agent.router, prefix="/api/agent", tags=["Agent"])

@app.get("/")
async def root():
    return {"message": "生活小助手 API 运行中", "version": "2.0.0"}
