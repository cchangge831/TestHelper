@echo off
chcp 65001 >nul
cd /d C:\Users\cchan\Desktop\Work\TestHelper\ENV_Manager

echo [ENV_Manager] 启动开发模式...
echo [ENV_Manager] 后端端口: 6688 | 前端端口: 5173

start "ENV_Manager-Backend" cmd /c "cd backend && python app.py"
start "ENV_Manager-Frontend" cmd /c "cd frontend && npm run dev"

timeout /t 3 >nul
start http://localhost:5173
