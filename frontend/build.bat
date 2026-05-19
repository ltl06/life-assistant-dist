@echo off
echo ========================================
echo   生活小助手 - 前端构建脚本
echo ========================================
echo.
echo 正在安装依赖并构建...
call npm install
if %errorlevel% neq 0 (
    echo.
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)
echo.
call npm run build
if %errorlevel% neq 0 (
    echo.
    echo [错误] 构建失败
    pause
    exit /b 1
)
echo.
echo ========================================
echo   构建完成！
echo   产物目录: dist\
echo ========================================
echo.
echo 生产部署提示：
echo 1. 将 dist\ 下的文件部署到 Web 服务器
echo 2. 配置 Web 服务器将 /api 请求代理到后端
echo 3. 后端使用 uvicorn main:app --host 0.0.0.0 --port 8000 运行
echo.
pause
