@echo off
echo ========================================
echo   生活小助手 - 后端启动脚本
echo ========================================
echo.
echo 正在安装 Python 依赖...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo [错误] 依赖安装失败，请确保已安装 Python 3.8+
    pause
    exit /b 1
)
echo.
echo 正在启动后端服务...
echo 访问地址: http://localhost:8000
echo API 文档:   http://localhost:8000/docs
echo.
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
