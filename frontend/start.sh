#!/bin/bash
echo "========================================"
echo "  生活小助手 - 前端启动脚本"
echo "========================================"
echo ""
echo "正在安装 Node.js 依赖..."
npm install
echo ""
echo "正在启动开发服务器..."
echo "前端访问:  http://localhost:5173"
echo "后端 API:  http://localhost:8000"
echo ""
echo "提示：后端必须先启动（运行 backend/start.sh）"
echo ""
npm run dev -- --host
