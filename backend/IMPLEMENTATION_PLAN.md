# 后端实现计划

## 📋 项目概述

本文档详细规划了"社会学大师陪伴智能体"后端服务的实现步骤，基于 **FastAPI + SQLite + Docker** 技术栈。

---

## 🎯 实现目标

1. ✅ 提供符合 API 规范的 RESTful 接口
2. ✅ 集成现有 AI 模块（RAG + Gemini）
3. ✅ 支持流式和非流式对话响应
4. ✅ 收集和存储用户反馈遥测数据
5. ✅ Docker 容器化部署
6. ✅ 完善的错误处理和日志记录
7. ✅ API 文档自动生成

---

## 📦 核心依赖包

### requirements.txt

```txt
# Web 框架
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# 数据库
sqlalchemy==2.0.25

# 数据验证
pydantic==2.5.3
pydantic-settings==2.1.0

# AI 相关（复用现有 ai/ 模块的依赖）
pinecone-client==3.0.0
langchain==0.1.0
langchain-core==0.1.0
langchain-google-genai==0.0.6
langchain-pinecone==0.0.1
langchain-text-splitters==0.0.1

# 工具库
python-dotenv==1.0.0

# 日志
loguru==0.7.2

# 测试
pytest==7.4.4
pytest-asyncio==0.23.3
httpx==0.26.0
```

---

## 📁 详细文件结构

```
isse-project/
├── backend/
│   ├── app/
│   │   ├── __init__.py                    # 包初始化
│   │   ├── main.py                        # FastAPI 应用入口
│   │   ├── config.py                      # 配置管理
│   │   ├── database.py                    # 数据库连接
│   │   ├── models.py                      # ORM 模型
│   │   ├── schemas.py                     # Pydantic 模型
│   │   │
│   │   ├── api/                           # API 路由
│   │   │   ├── __init__.py
│   │   │   ├── chat.py                    # Chat 接口
│   │   │   └── telemetry.py               # Telemetry 接口
│   │   │
│   │   ├── services/                      # 业务逻辑
│   │   │   ├── __init__.py
│   │   │   ├── ai_service.py              # AI 服务
│   │   │   └── telemetry_service.py       # 遥测服务
│   │   │
│   │   └── utils/                         # 工具函数
│   │       ├── __init__.py
│   │       ├── logger.py                  # 日志配置
│   │       └── exceptions.py              # 自定义异常
│   │
│   ├── tests/                             # 测试文件
│   │   ├── __init__.py
│   │   ├── test_chat.py
│   │   └── test_telemetry.py
│   │
│   ├── scripts/                           # 脚本工具
│   │   ├── init_db.py                     # 数据库初始化
│   │   └── test_api.py                    # API 测试
│   │
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
│
├── ai/                                    # 现有 AI 模块
├── data/                                  # 知识库数据
└── docs/api/api.md                        # API 规范
```

---

## 🔨 分阶段实现步骤

### Phase 1: 项目基础搭建

**目标**: 创建项目结构，配置基础组件

**任务清单**:
- [ ] 创建目录结构
- [ ] 配置管理 ([`config.py`](app/config.py))
- [ ] 数据库连接 ([`database.py`](app/database.py))
- [ ] ORM 模型定义 ([`models.py`](app/models.py))
- [ ] Pydantic 模型 ([`schemas.py`](app/schemas.py))
- [ ] 环境变量配置 (`.env`)

**关键代码示例**:

#### config.py
```python
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Sociology Master Chat API"
    API_V1_PREFIX: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./backend.db"
    PINECONE_API_KEY: str
    GEMINI_API_KEY: str
    PINECONE_INDEX_NAME: str = "sociology-master"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"

settings = Settings()
```

---

### Phase 2: AI 服务集成

**目标**: 封装现有 AI 模块，提供统一接口

**任务清单**:
- [ ] 创建 AI Service 类
- [ ] 实现 character 到 namespace 映射
- [ ] 实现 RAG 检索逻辑
- [ ] 实现非流式响应生成
- [ ] 实现流式响应生成（SSE）
- [ ] 错误处理和日志记录

**核心逻辑**:

```python
class AIService:
    def __init__(self):
        # 初始化 Pinecone、Gemini、VectorStore
        
    async def chat(
        self,
        character: str,
        messages: List[Message],
        temperature: float,
        stream: bool
    ) -> Union[ChatResponse, AsyncGenerator]:
        # 1. 提取用户问题
        # 2. 确定 namespace
        # 3. RAG 检索
        # 4. 构建 Prompt
        # 5. 生成响应
```

---

### Phase 3: API 路由实现

**目标**: 实现符合规范的 API 接口

**任务清单**:
- [ ] Chat API ([`api/chat.py`](app/api/chat.py))
  - [ ] 非流式响应
  - [ ] 流式响应（SSE）
  - [ ] 参数验证
  - [ ] 错误处理
- [ ] Telemetry API ([`api/telemetry.py`](app/api/telemetry.py))
  - [ ] 数据验证
  - [ ] 数据库存储
  - [ ] 错误处理
- [ ] 主应用入口 ([`main.py`](app/main.py))
  - [ ] 路由注册
  - [ ] CORS 配置
  - [ ] 启动事件

**API 端点**:
- `POST /api/v1/chat` - 对话接口
- `POST /api/v1/telemetry` - 遥测接口
- `GET /health` - 健康检查

---

### Phase 4: 辅助功能

**目标**: 完善日志、异常处理等辅助功能

**任务清单**:
- [ ] 日志配置 ([`utils/logger.py`](app/utils/logger.py))
- [ ] 自定义异常 ([`utils/exceptions.py`](app/utils/exceptions.py))
- [ ] Telemetry Service ([`services/telemetry_service.py`](app/services/telemetry_service.py))

---

### Phase 5: Docker 容器化

**目标**: 实现容器化部署

**任务清单**:
- [ ] 编写 Dockerfile
- [ ] 编写 docker-compose.yml
- [ ] 配置环境变量
- [ ] 测试容器构建和运行

**Dockerfile 示例**:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./app ./app
COPY ./ai ../ai
COPY ./data ../data
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### Phase 6: 测试和文档

**目标**: 编写测试用例和使用文档

**任务清单**:
- [ ] 单元测试
  - [ ] Chat API 测试
  - [ ] Telemetry API 测试
  - [ ] AI Service 测试
- [ ] 集成测试
- [ ] API 测试脚本
- [ ] README 文档
- [ ] 部署文档

---

## 📊 实现进度表

| 阶段 | 任务 | 预计时间 | 状态 |
|------|------|----------|------|
| Phase 1 | 项目基础搭建 | 2天 | ⏳ 待开始 |
| Phase 2 | AI 服务集成 | 2天 | ⏳ 待开始 |
| Phase 3 | API 路由实现 | 2天 | ⏳ 待开始 |
| Phase 4 | 辅助功能 | 1天 | ⏳ 待开始 |
| Phase 5 | Docker 容器化 | 1天 | ⏳ 待开始 |
| Phase 6 | 测试和文档 | 2天 | ⏳ 待开始 |

**总计**: 10天

---

## 🚀 快速启动指南

### 1. 环境准备

```bash
cd isse-project/backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API 密钥
```

### 2. 初始化数据库

```bash
python scripts/init_db.py
```

### 3. 启动服务

```bash
# 开发模式
uvicorn app.main:app --reload --port 8000

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. 访问 API 文档

打开浏览器访问: `http://localhost:8000/docs`

---

## 🔍 关键技术点

### 1. AI Service 集成

**挑战**: 如何将现有的 [`chat_agent.py`](../ai/chat_agent.py) 集成到 FastAPI 中

**解决方案**:
- 创建 AIService 类封装 RAG 逻辑
- 使用单例模式避免重复初始化
- 异步处理提高性能

### 2. 流式响应（SSE）

**挑战**: 实现 Server-Sent Events 流式输出

**解决方案**:
```python
from fastapi.responses import StreamingResponse

async def generate_stream():
    for chunk in ai_response:
        yield f"data: {json.dumps(chunk)}\n\n"
    yield "data: [DONE]\n\n"

return StreamingResponse(
    generate_stream(),
    media_type="text/event-stream"
)
```

### 3. 数据库会话管理

**挑战**: SQLAlchemy 会话的正确使用

**解决方案**:
```python
from fastapi import Depends

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/v1/telemetry")
async def telemetry(
    request: TelemetryRequest,
    db: Session = Depends(get_db)
):
    # 使用 db 进行数据库操作
```

---

## 📝 开发规范

### 代码风格
- 遵循 PEP 8 规范
- 使用类型注解
- 编写清晰的文档字符串

### 提交规范
- feat: 新功能
- fix: 修复 bug
- docs: 文档更新
- refactor: 代码重构
- test: 测试相关

### 分支策略
- main: 生产环境
- develop: 开发环境
- feature/*: 功能分支

---

## 🐛 常见问题

### Q1: Pinecone 连接失败
**A**: 检查 API 密钥是否正确，确保网络可访问 Pinecone 服务

### Q2: SQLite 数据库锁定
**A**: 使用 `check_same_thread=False` 配置，避免多线程问题

### Q3: CORS 错误
**A**: 在 [`main.py`](app/main.py) 中正确配置 CORS 中间件

---

## 📚 相关文档

- [架构设计文档](./ARCHITECTURE.md)
- [数据库设计文档](./DATABASE_DESIGN.md)
- [API 规范](../docs/api/api.md)
- [AI 模块说明](../ai/ai.md)

---

## ✅ 实施检查清单

### 开发前
- [ ] 阅读 API 规范文档
- [ ] 理解现有 AI 模块
- [ ] 准备开发环境
- [ ] 获取 API 密钥

### 开发中
- [ ] 按阶段实施
- [ ] 编写单元测试
- [ ] 记录开发日志
- [ ] 代码审查

### 开发后
- [ ] 完整测试
- [ ] 性能优化
- [ ] 文档完善
- [ ] 部署验证

---

## 🎉 下一步行动

准备好开始实施了吗？建议按以下顺序进行：

1. **立即开始**: Phase 1 - 项目基础搭建
2. **核心功能**: Phase 2 & 3 - AI 集成和 API 实现
3. **完善优化**: Phase 4 & 5 - 辅助功能和容器化
4. **质量保证**: Phase 6 - 测试和文档

**预计完成时间**: 10个工作日

**建议**: 可以切换到 Code 模式开始实际编码！