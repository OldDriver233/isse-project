@echo off
echo ========================================
echo   Tocqueville AI 前端启动脚本
echo ========================================
echo.

REM 检查是否安装了 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.x
    pause
    exit /b 1
)

echo [信息] 检测到 Python 版本:
python --version

echo.
echo [信息] 正在启动 HTTP 服务器...
echo [信息] 前端地址: http://localhost:3000
echo [信息] 测试页面: http://localhost:3000/test.html
echo.
echo [提示] 按 Ctrl+C 停止服务器
echo.

cd /d %~dp0
python -m http.server 3000
