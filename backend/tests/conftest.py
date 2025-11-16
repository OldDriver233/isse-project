"""
Pytest 配置文件

提供测试所需的 fixtures 和配置。
"""

import os
import sys
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import Base, get_db
from app.main import app
from app.config import settings


# ==================== 数据库 Fixtures ====================

@pytest.fixture(scope="function")
def test_db() -> Generator[Session, None, None]:
    """
    创建测试数据库会话
    
    每个测试函数使用独立的内存数据库，测试结束后自动清理。
    """
    # 创建内存数据库引擎
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    # 创建会话
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # 清理所有表
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db: Session) -> Generator[TestClient, None, None]:
    """
    创建测试客户端
    
    使用测试数据库覆盖应用的数据库依赖。
    """
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


# ==================== 测试数据 Fixtures ====================

@pytest.fixture
def sample_user_id() -> str:
    """示例用户 ID"""
    return "test-user-123e4567-e89b-12d3-a456-426614174000"


@pytest.fixture
def sample_messages() -> list:
    """示例消息列表"""
    return [
        {
            "role": "user",
            "content": "托克维尔对美国民主的看法是什么？"
        },
        {
            "role": "assistant",
            "content": "我曾亲身踏足美洲大陆，深入观察了这个新兴国家的民主制度..."
        }
    ]


@pytest.fixture
def sample_rating() -> dict:
    """示例评分数据"""
    return {
        "overall_rating": 8,
        "comment": "回答很有深度，但有些地方过于学术化"
    }


@pytest.fixture
def sample_telemetry_request(sample_user_id: str, sample_rating: dict, sample_messages: list) -> dict:
    """示例 Telemetry 请求数据"""
    return {
        "user_id": sample_user_id,
        "rating": sample_rating,
        "messages": sample_messages
    }


@pytest.fixture
def sample_chat_request() -> dict:
    """示例 Chat 请求数据"""
    return {
        "character": "tocqueville",
        "messages": [
            {
                "role": "user",
                "content": "你好，请介绍一下你自己"
            }
        ],
        "stream": False,
        "temperature": 0.5
    }


# ==================== Mock Fixtures ====================

@pytest.fixture
def mock_ai_response() -> dict:
    """Mock AI 服务响应"""
    return {
        "result": {
            "message": {
                "role": "assistant",
                "content": "我是阿历克西·德·托克维尔，法国政治思想家和历史学家..."
            },
            "finish_reason": "stop"
        },
        "usage": {
            "prompt_tokens": 50,
            "completion_tokens": 100,
            "total_tokens": 150
        },
        "created": 1234567890,
        "id": "test-response-id"
    }


# ==================== 环境配置 ====================

@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """
    设置测试环境变量
    
    在所有测试开始前执行一次。
    """
    # 设置测试环境变量
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["PINECONE_API_KEY"] = "test-pinecone-key"
    os.environ["GEMINI_API_KEY"] = "test-gemini-key"
    os.environ["LOG_LEVEL"] = "ERROR"  # 减少测试时的日志输出
    
    yield
    
    # 清理（如果需要）
    pass


# ==================== 辅助函数 ====================

def assert_response_structure(response_data: dict, expected_keys: list):
    """
    断言响应数据包含预期的键
    
    Args:
        response_data: 响应数据字典
        expected_keys: 预期的键列表
    """
    for key in expected_keys:
        assert key in response_data, f"响应缺少键: {key}"


def assert_error_response(response_data: dict, expected_code: str = None):
    """
    断言错误响应格式
    
    Args:
        response_data: 响应数据字典
        expected_code: 预期的错误代码（可选）
    """
    assert "error" in response_data, "错误响应缺少 'error' 字段"
    assert "code" in response_data["error"], "错误响应缺少 'code' 字段"
    assert "message" in response_data["error"], "错误响应缺少 'message' 字段"
    
    if expected_code:
        assert response_data["error"]["code"] == expected_code, \
            f"错误代码不匹配: 期望 {expected_code}, 实际 {response_data['error']['code']}"