# 测试文档

本目录包含后端 API 的完整测试套件。

## 📋 目录结构

```
tests/
├── __init__.py                 # 测试模块初始化
├── conftest.py                 # Pytest 配置和 fixtures
├── test_models.py              # 数据库模型测试
├── test_telemetry_api.py       # Telemetry API 测试
├── test_chat_api.py            # Chat API 测试
├── test_services.py            # 服务层测试
├── test_utils.py               # 工具函数测试
├── test_integration.py         # 集成测试
└── README.md                   # 本文档
```

## 🧪 测试类型

### 1. 单元测试

- **test_models.py**: 测试数据库模型的创建、验证和约束
- **test_services.py**: 测试业务逻辑服务层
- **test_utils.py**: 测试工具函数和辅助模块

### 2. API 测试

- **test_telemetry_api.py**: 测试用户反馈遥测 API
- **test_chat_api.py**: 测试 AI 对话 API

### 3. 集成测试

- **test_integration.py**: 测试多个组件协同工作的端到端场景

## 🚀 运行测试

### 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 运行所有测试

```bash
# 在 backend 目录下运行
pytest

# 或使用详细输出
pytest -v

# 显示测试覆盖率
pytest --cov=app --cov-report=html
```

### 运行特定测试文件

```bash
# 运行模型测试
pytest tests/test_models.py

# 运行 API 测试
pytest tests/test_telemetry_api.py
pytest tests/test_chat_api.py

# 运行集成测试
pytest tests/test_integration.py
```

### 运行特定测试类或方法

```bash
# 运行特定测试类
pytest tests/test_models.py::TestTelemetryModel

# 运行特定测试方法
pytest tests/test_models.py::TestTelemetryModel::test_create_telemetry

# 使用关键字过滤
pytest -k "telemetry"
```

### 并行运行测试

```bash
# 安装 pytest-xdist
pip install pytest-xdist

# 使用多个 CPU 核心运行
pytest -n auto
```

## 📊 测试覆盖率

生成测试覆盖率报告：

```bash
# 生成 HTML 报告
pytest --cov=app --cov-report=html

# 查看报告
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

生成终端报告：

```bash
pytest --cov=app --cov-report=term-missing
```

## 🔧 测试配置

### conftest.py

提供了以下 fixtures：

- `test_db`: 测试数据库会话（内存 SQLite）
- `client`: FastAPI 测试客户端
- `sample_user_id`: 示例用户 ID
- `sample_messages`: 示例消息列表
- `sample_rating`: 示例评分数据
- `sample_telemetry_request`: 示例 Telemetry 请求
- `sample_chat_request`: 示例 Chat 请求
- `mock_ai_response`: Mock AI 服务响应

### 环境变量

测试会自动设置以下环境变量：

```bash
DATABASE_URL=sqlite:///:memory:
PINECONE_API_KEY=test-pinecone-key
GEMINI_API_KEY=test-gemini-key
LOG_LEVEL=ERROR
```

## 📝 测试统计

### 测试数量

- **模型测试**: ~20 个测试
- **Telemetry API 测试**: ~30 个测试
- **Chat API 测试**: ~25 个测试
- **服务层测试**: ~25 个测试
- **工具函数测试**: ~20 个测试
- **集成测试**: ~15 个测试

**总计**: ~135 个测试

### 覆盖的功能

✅ 数据库模型创建和验证  
✅ 数据约束检查  
✅ API 端点正常流程  
✅ API 错误处理  
✅ 数据验证  
✅ 服务层业务逻辑  
✅ 统计功能  
✅ 多用户场景  
✅ 并发处理  
✅ 边界情况  
✅ 端到端工作流  

## 🐛 调试测试

### 查看详细输出

```bash
# 显示 print 语句
pytest -s

# 显示详细信息
pytest -v

# 组合使用
pytest -sv
```

### 在失败时进入调试器

```bash
# 安装 pytest-pdb
pip install pytest-pdb

# 失败时自动进入 pdb
pytest --pdb

# 在第一个失败时停止
pytest -x --pdb
```

### 只运行失败的测试

```bash
# 第一次运行
pytest

# 只重新运行失败的测试
pytest --lf

# 先运行失败的，再运行其他的
pytest --ff
```

## 📈 持续集成

### GitHub Actions 示例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        cd backend
        pytest --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        file: ./backend/coverage.xml
```

## 🎯 最佳实践

### 1. 测试命名

- 使用描述性的测试名称
- 遵循 `test_<功能>_<场景>` 模式
- 例如: `test_create_telemetry_success`

### 2. 测试组织

- 使用测试类组织相关测试
- 每个测试应该独立运行
- 避免测试之间的依赖

### 3. 使用 Fixtures

- 复用测试数据和设置
- 保持测试代码简洁
- 使用适当的 scope（function, class, module, session）

### 4. Mock 外部依赖

- Mock AI 服务调用
- Mock 外部 API
- 使用内存数据库进行测试

### 5. 断言清晰

- 使用明确的断言消息
- 一个测试关注一个方面
- 验证预期行为和错误情况

## 🔍 常见问题

### Q: 测试运行很慢怎么办？

A: 使用并行测试：
```bash
pytest -n auto
```

### Q: 如何跳过某些测试？

A: 使用 pytest 标记：
```python
@pytest.mark.skip(reason="暂时跳过")
def test_something():
    pass
```

### Q: 如何测试异步函数？

A: 使用 `pytest-asyncio`：
```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

### Q: 数据库测试后如何清理？

A: 使用 fixture 的 teardown：
```python
@pytest.fixture
def test_db():
    # Setup
    db = create_test_db()
    yield db
    # Teardown
    db.close()
    cleanup_test_db()
```

## 📚 参考资料

- [Pytest 文档](https://docs.pytest.org/)
- [FastAPI 测试文档](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy 测试](https://docs.sqlalchemy.org/en/14/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)

## 🤝 贡献指南

添加新测试时：

1. 选择合适的测试文件或创建新文件
2. 使用现有的 fixtures
3. 遵循命名约定
4. 添加清晰的文档字符串
5. 确保测试可以独立运行
6. 运行所有测试确保没有破坏现有功能

## 📞 联系方式

如有问题或建议，请联系开发团队或提交 Issue。