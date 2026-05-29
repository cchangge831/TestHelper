@echo off
chcp 65001 >nul
cd /d C:\Repo\codeRepo\TestHelper\ENV_Manager

echo [ENV_Manager] 构建前端...
cd frontend
call npm run build >nul 2>&1
if %errorlevel% neq 0 (
    echo [ENV_Manager] 前端构建失败，请检查代码
    pause
    exit /b 1
)

echo [ENV_Manager] 启动服务...
cd /d C:\Repo\codeRepo\TestHelper\ENV_Manager\backend
start "" pythonw.exe tray_launcher.py

timeout /t 2 >nul
start http://localhost:6688
