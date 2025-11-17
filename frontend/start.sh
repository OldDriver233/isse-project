#!/bin/bash

echo "========================================"
echo "  Tocqueville AI 前端启动脚本"
echo "========================================"
echo ""

# 检查是否安装了 Python
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null
then
    echo "[错误] 未检测到 Python，请先安装 Python 3.x"
    exit 1
fi

# 使用 python3 或 python
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
else
    PYTHON_CMD=python
fi

echo "[信息] 检测到 Python 版本:"
$PYTHON_CMD --version

echo ""
echo "[信息] 正在启动 HTTP 服务器..."
echo "[信息] 前端地址: http://localhost:3000"
echo "[信息] 测试页面: http://localhost:3000/test.html"
echo ""
echo "[提示] 按 Ctrl+C 停止服务器"
echo ""

cd "$(dirname "$0")"
$PYTHON_CMD -m http.server 3000
