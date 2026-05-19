@echo off
echo ========================================
echo   生活小助手 - 前端启动脚本
echo ========================================
echo.
echo 正在安装 Node.js 依赖...
call npm install
if %errorlevel% neq 0 (
    echo.
    echo [错误] 依赖安装失败，请确保已安装 Node.js 18+
    pause
    exit /b 1
)
echo.
echo 正在启动开发服务器...
echo 前端访问:  http://localhost:5173
echo 后端 API:  http://localhost:8000
echo.
echo 提示：后端必须先启动（运行 backend/start.bat）
echo.
call npm run dev -- --host
