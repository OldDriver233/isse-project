#!/bin/bash

# 安装测试依赖脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📦 安装测试依赖包...${NC}"
echo ""

# 安装测试相关的包
pip install pytest>=7.4.0
pip install pytest-asyncio>=0.23.0
pip install pytest-cov>=4.1.0
pip install pytest-xdist>=3.5.0
pip install pytest-html>=4.1.0

echo ""
echo -e "${GREEN}✅ 测试依赖安装完成！${NC}"
echo ""
echo "现在可以运行测试了："
echo "  pytest                    # 运行所有测试"
echo "  pytest --cov=app          # 带覆盖率"
echo "  pytest -n auto            # 并行运行"
echo "  ./run_tests.sh            # 使用测试脚本"