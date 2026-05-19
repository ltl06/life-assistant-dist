# 生活小助手 (Life Assistant) v2.0

一个帮助你管理健康、财务、待办和习惯的私人助理 Web 应用。

## 功能

- **健康追踪**：记录体重、步数、睡眠时长、心情，查看趋势图表
- **财务记账**：收入/支出随手记，饼图分析消费结构，月度统计结余
- **月度预算**：为每个支出分类设定月度预算，超支自动预警
- **习惯日历**：可视化打卡日历，追踪连续打卡天数
- **效率工具**：待办清单（高/中/低优先级）、习惯打卡、定时提醒
- **日记本**：每日随笔，心情标签，搜索功能，连续记录天数
- **天气 + 每日建议**：自动获取当地天气，附带穿衣/运动建议
- **快捷记录**：按 `Ctrl+K` 呼出浮窗，快捷记账/步数/体重/睡眠
- **数据导出**：健康、财务、日记、待办全部支持 CSV 导出
- **AI 助手**：对话式交互，获取健康建议、理财规划、日程安排

## 快速启动

### 1. 启动后端

**Windows:**
```
cd backend
start.bat
```

**Linux / Mac:**
```
cd backend
chmod +x start.sh
./start.sh
```

后端运行在 http://localhost:8000
API 文档: http://localhost:8000/docs

### 2. 启动前端（新开终端）

**Windows:**
```
cd frontend
start.bat
```

**Linux / Mac:**
```
cd frontend
chmod +x start.sh
./start.sh
```

前端运行在 http://localhost:5173

### 3. 打开浏览器

访问 **http://localhost:5173**，注册账号后即可使用。

## 配置（可选）

编辑 `backend/.env`：

```env
OPENAI_API_KEY=sk-your-openai-key
# 或使用 DeepSeek
DEEPSEEK_API_KEY=sk-your-deepseek-key
# 天气功能（需要 WeatherAPI.com 免费 API Key）
WEATHER_API_KEY=your-weatherapi-key
# 在设置页面填写城市名即可显示天气
```

## 系统要求

- **后端**: Python 3.8+
- **前端**: Node.js 18+

## 快捷键

- `Ctrl+K` (或点击右下角 ⚡ 按钮)：呼出快捷记录浮窗
  - 输入「记账 35 午餐」→ 自动记录支出
  - 输入「走了 8000 步」→ 自动记录步数
  - 输入「体重 65」→ 自动记录体重
  - 输入「睡了 7.5 小时」→ 自动记录睡眠

## 项目结构

```
life-assistant-dist/
├── backend/
│   ├── main.py
│   ├── database.py           # 数据库模型
│   ├── requirements.txt
│   ├── .env                 # 环境变量
│   ├── routers/
│   │   ├── auth.py          # 用户认证
│   │   ├── health.py        # 健康记录
│   │   ├── finance.py       # 财务记账
│   │   ├── productivity.py  # 待办/提醒
│   │   ├── budget.py        # 月度预算
│   │   ├── diary.py         # 日记笔记
│   │   ├── habit_tracker.py # 习惯打卡
│   │   ├── weather.py       # 天气
│   │   ├── export.py         # CSV 导出
│   │   ├── quick_add.py      # 快捷记录
│   │   └── ai_assistant.py  # AI 对话
│   ├── start.bat
│   └── start.sh
│
└── frontend/
    ├── src/
    │   ├── pages/
    │   │   ├── Dashboard.jsx    # 仪表盘
    │   │   ├── Health.jsx       # 健康
    │   │   ├── Finance.jsx       # 财务
    │   │   ├── Budget.jsx       # 预算
    │   │   ├── Productivity.jsx # 效率
    │   │   ├── CalendarPage.jsx # 习惯日历
    │   │   ├── Diary.jsx        # 日记
    │   │   ├── AIChat.jsx       # AI 对话
    │   │   └── Settings.jsx     # 设置
    │   ├── components/
    │   │   ├── Sidebar.jsx
    │   │   └── QuickFloat.jsx    # 快捷记录浮窗
    │   ├── stores/authStore.js
    │   └── utils/api.js
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    └── ...
```

## 生产部署

1. 前端构建: `cd frontend && build.bat`（或 `npm run build`）
2. 部署 `frontend/dist/` 到 Web 服务器（Nginx、Caddy 等）
3. 配置反向代理 `/api` 到 `http://localhost:8000`
4. 后端: `uvicorn main:app --host 0.0.0.0 --port 8000`
