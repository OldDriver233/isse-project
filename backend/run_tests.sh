#!/bin/bash

# 测试运行脚本
# 提供多种测试运行选项

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 显示帮助信息
show_help() {
    cat << EOF
测试运行脚本

用法: ./run_tests.sh [选项]

选项:
    -h, --help              显示此帮助信息
    -a, --all               运行所有测试（默认）
    -u, --unit              只运行单元测试
    -i, --integration       只运行集成测试
    -c, --coverage          生成覆盖率报告
    -v, --verbose           详细输出
    -f, --fast              快速模式（并行运行）
    -w, --watch             监视模式（文件变化时自动运行）
    -m, --markers MARKERS   运行特定标记的测试
    -k, --keyword KEYWORD   运行匹配关键字的测试
    --html                  生成 HTML 测试报告
    --failed                只运行上次失败的测试

示例:
    ./run_tests.sh                          # 运行所有测试
    ./run_tests.sh -c                       # 运行测试并生成覆盖率报告
    ./run_tests.sh -v -f                    # 详细输出 + 并行运行
    ./run_tests.sh -k "telemetry"           # 只运行包含 telemetry 的测试
    ./run_tests.sh --failed                 # 只运行上次失败的测试

EOF
}

# 检查 pytest 是否安装
check_pytest() {
    if ! command -v pytest &> /dev/null; then
        print_error "pytest 未安装"
        print_info "请运行: pip install -r requirements.txt"
        exit 1
    fi
}

# 默认参数
VERBOSE=""
COVERAGE=""
PARALLEL=""
WATCH=""
MARKERS=""
KEYWORD=""
HTML=""
FAILED=""
TEST_PATH="tests/"

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -a|--all)
            TEST_PATH="tests/"
            shift
            ;;
        -u|--unit)
            TEST_PATH="tests/test_models.py tests/test_services.py tests/test_utils.py"
            shift
            ;;
        -i|--integration)
            TEST_PATH="tests/test_integration.py"
            shift
            ;;
        -c|--coverage)
            COVERAGE="--cov=app --cov-report=html --cov-report=term-missing"
            shift
            ;;
        -v|--verbose)
            VERBOSE="-v"
            shift
            ;;
        -f|--fast)
            PARALLEL="-n auto"
            shift
            ;;
        -w|--watch)
            WATCH="--watch"
            shift
            ;;
        -m|--markers)
            MARKERS="-m $2"
            shift 2
            ;;
        -k|--keyword)
            KEYWORD="-k $2"
            shift 2
            ;;
        --html)
            HTML="--html=test_report.html --self-contained-html"
            shift
            ;;
        --failed)
            FAILED="--lf"
            shift
            ;;
        *)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 检查依赖
check_pytest

# 打印测试信息
print_info "开始运行测试..."
echo ""

# 构建 pytest 命令
PYTEST_CMD="pytest $TEST_PATH $VERBOSE $COVERAGE $PARALLEL $MARKERS $KEYWORD $HTML $FAILED"

# 如果是监视模式
if [ -n "$WATCH" ]; then
    if ! command -v pytest-watch &> /dev/null; then
        print_warning "pytest-watch 未安装，安装中..."
        pip install pytest-watch
    fi
    print_info "进入监视模式（按 Ctrl+C 退出）"
    ptw -- $PYTEST_CMD
    exit 0
fi

# 运行测试
print_info "执行命令: $PYTEST_CMD"
echo ""

if $PYTEST_CMD; then
    echo ""
    print_success "所有测试通过！"
    
    # 如果生成了覆盖率报告
    if [ -n "$COVERAGE" ]; then
        echo ""
        print_info "覆盖率报告已生成: htmlcov/index.html"
        print_info "查看报告:"
        echo "  - macOS:   open htmlcov/index.html"
        echo "  - Linux:   xdg-open htmlcov/index.html"
        echo "  - Windows: start htmlcov/index.html"
    fi
    
    # 如果生成了 HTML 报告
    if [ -n "$HTML" ]; then
        echo ""
        print_info "测试报告已生成: test_report.html"
    fi
    
    exit 0
else
    echo ""
    print_error "测试失败！"
    print_info "提示:"
    echo "  - 使用 -v 查看详细输出"
    echo "  - 使用 --failed 只运行失败的测试"
    echo "  - 使用 -k 'test_name' 运行特定测试"
    exit 1
fi