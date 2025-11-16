"""
工具函数测试

测试应用中的工具函数和辅助模块。
"""

import pytest
from fastapi import FastAPI, Request, HTTPException
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.utils.exceptions import (
    AppException,
    ValidationException,
    AIServiceException,
    DatabaseException
)


class TestCustomExceptions:
    """自定义异常测试"""
    
    def test_app_exception_basic(self):
        """测试基础应用异常"""
        exc = AppException(
            message="测试错误",
            code="TEST_ERROR"
        )
        
        assert exc.message == "测试错误"
        assert exc.code == "TEST_ERROR"
        assert exc.status_code == 500
        assert exc.details is None
    
    def test_app_exception_with_details(self):
        """测试带详情的应用异常"""
        exc = AppException(
            message="测试错误",
            code="TEST_ERROR",
            details="详细错误信息"
        )
        
        assert exc.details == "详细错误信息"
    
    def test_app_exception_custom_status_code(self):
        """测试自定义状态码"""
        exc = AppException(
            message="测试错误",
            code="TEST_ERROR",
            status_code=400
        )
        
        assert exc.status_code == 400
    
    def test_validation_exception(self):
        """测试验证异常"""
        exc = ValidationException(
            message="验证失败",
            details="字段 X 不能为空"
        )
        
        assert exc.code == "VALIDATION_ERROR"
        assert exc.status_code == 400
        assert exc.message == "验证失败"
        assert exc.details == "字段 X 不能为空"
    
    def test_ai_service_exception(self):
        """测试 AI 服务异常"""
        exc = AIServiceException(
            message="AI 服务错误",
            details="模型不可用"
        )
        
        assert exc.code == "AI_SERVICE_ERROR"
        assert exc.message == "AI 服务错误"
        assert exc.details == "模型不可用"
    
    def test_database_exception(self):
        """测试数据库异常"""
        exc = DatabaseException(
            message="数据库连接失败",
            details="无法连接到数据库"
        )
        
        assert exc.code == "DATABASE_ERROR"
        assert exc.message == "数据库连接失败"
        assert exc.details == "无法连接到数据库"


class TestHealthEndpoint:
    """健康检查端点测试"""
    
    def test_health_check(self, client: TestClient):
        """测试健康检查端点"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert data["status"] == "healthy"
    
    def test_root_endpoint(self, client: TestClient):
        """测试根端点"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert data["docs"] == "/docs"


class TestSchemaValidation:
    """Schema 验证测试"""
    
    def test_message_role_validation(self):
        """测试消息角色验证"""
        from app.schemas import Message
        
        # 有效角色
        valid_roles = ["system", "user", "assistant"]
        for role in valid_roles:
            msg = Message(role=role, content="测试")
            assert msg.role == role
        
        # 无效角色
        with pytest.raises(Exception):
            Message(role="invalid_role", content="测试")
    
    def test_rating_validation(self):
        """测试评分验证"""
        from app.schemas import Rating
        
        # 有效评分
        for rating in range(1, 11):
            r = Rating(overall_rating=rating)
            assert r.overall_rating == rating
        
        # 无效评分（过低）
        with pytest.raises(Exception):
            Rating(overall_rating=0)
        
        # 无效评分（过高）
        with pytest.raises(Exception):
            Rating(overall_rating=11)
    
    def test_chat_request_validation(self):
        """测试 Chat 请求验证"""
        from app.schemas import ChatRequest, Message
        
        # 有效请求
        request = ChatRequest(
            character="tocqueville",
            messages=[Message(role="user", content="测试")],
            stream=False,
            temperature=0.5
        )
        
        assert request.character == "tocqueville"
        assert len(request.messages) == 1
        assert request.temperature == 0.5
    
    def test_chat_request_empty_messages(self):
        """测试空消息列表验证"""
        from app.schemas import ChatRequest
        
        with pytest.raises(Exception):
            ChatRequest(
                character="tocqueville",
                messages=[],
                stream=False
            )
    
    def test_chat_request_temperature_range(self):
        """测试温度参数范围验证"""
        from app.schemas import ChatRequest, Message
        
        # 有效范围
        for temp in [0.0, 0.5, 1.0, 1.5, 2.0]:
            request = ChatRequest(
                character="tocqueville",
                messages=[Message(role="user", content="测试")],
                temperature=temp
            )
            assert request.temperature == temp
        
        # 无效范围（过低）
        with pytest.raises(Exception):
            ChatRequest(
                character="tocqueville",
                messages=[Message(role="user", content="测试")],
                temperature=-0.1
            )
        
        # 无效范围（过高）
        with pytest.raises(Exception):
            ChatRequest(
                character="tocqueville",
                messages=[Message(role="user", content="测试")],
                temperature=2.1
            )
    
    def test_telemetry_request_validation(self):
        """测试 Telemetry 请求验证"""
        from app.schemas import TelemetryRequest, Rating, Message
        
        request = TelemetryRequest(
            user_id="test-user-123",
            rating=Rating(overall_rating=8, comment="很好"),
            messages=[Message(role="user", content="测试")]
        )
        
        assert request.user_id == "test-user-123"
        assert request.rating.overall_rating == 8
        assert len(request.messages) == 1


class TestConfigSettings:
    """配置设置测试"""
    
    def test_settings_defaults(self):
        """测试默认配置"""
        from app.config import settings
        
        assert settings.PROJECT_NAME is not None
        assert settings.API_V1_PREFIX == "/api/v1"
        assert settings.VERSION is not None
        assert settings.DEFAULT_TEMPERATURE == 0.5
        assert settings.RAG_TOP_K == 4
    
    def test_settings_available_namespaces(self):
        """测试可用命名空间"""
        from app.config import settings
        
        assert "tocqueville" in settings.AVAILABLE_NAMESPACES
        assert "common" in settings.AVAILABLE_NAMESPACES
    
    def test_settings_allowed_origins(self):
        """测试 CORS 允许的源"""
        from app.config import settings
        
        assert isinstance(settings.ALLOWED_ORIGINS, list)
        assert len(settings.ALLOWED_ORIGINS) > 0


class TestDatabaseConnection:
    """数据库连接测试"""
    
    def test_database_session_creation(self, test_db):
        """测试数据库会话创建"""
        assert test_db is not None
        
        # 测试基本查询
        from app.models import Telemetry
        result = test_db.query(Telemetry).all()
        assert isinstance(result, list)
    
    def test_database_transaction_rollback(self, test_db):
        """测试数据库事务回滚"""
        from app.models import Telemetry
        
        # 创建一个记录
        telemetry = Telemetry(
            user_id="test-rollback",
            overall_rating=5,
            messages='[{"role": "user", "content": "测试"}]'
        )
        
        test_db.add(telemetry)
        test_db.flush()
        
        # 回滚
        test_db.rollback()
        
        # 验证记录未保存
        result = test_db.query(Telemetry)\
            .filter(Telemetry.user_id == "test-rollback")\
            .first()
        
        assert result is None
    
    def test_database_transaction_commit(self, test_db):
        """测试数据库事务提交"""
        from app.models import Telemetry
        
        # 创建一个记录
        telemetry = Telemetry(
            user_id="test-commit",
            overall_rating=7,
            messages='[{"role": "user", "content": "测试"}]'
        )
        
        test_db.add(telemetry)
        test_db.commit()
        
        # 验证记录已保存
        result = test_db.query(Telemetry)\
            .filter(Telemetry.user_id == "test-commit")\
            .first()
        
        assert result is not None
        assert result.user_id == "test-commit"


class TestMiddleware:
    """中间件测试"""
    
    def test_cors_middleware(self, client: TestClient):
        """测试 CORS 中间件"""
        response = client.options(
            "/api/v1/chat",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST"
            }
        )
        
        # CORS 预检请求应该成功
        assert response.status_code in [200, 204]
    
    def test_request_logging_middleware(self, client: TestClient):
        """测试请求日志中间件"""
        # 发送请求
        response = client.get("/health")
        
        # 请求应该成功处理
        assert response.status_code == 200
        
        # 中间件应该添加请求 ID（如果实现了）
        # 这取决于具体的中间件实现


class TestErrorHandling:
    """错误处理测试"""
    
    def test_404_error(self, client: TestClient):
        """测试 404 错误"""
        response = client.get("/non-existent-endpoint")
        
        assert response.status_code == 404
    
    def test_405_method_not_allowed(self, client: TestClient):
        """测试 405 方法不允许"""
        # GET 方法不支持 /api/v1/chat
        response = client.get("/api/v1/chat")
        
        assert response.status_code == 405
    
    def test_422_validation_error(self, client: TestClient):
        """测试 422 验证错误"""
        # 发送无效数据
        response = client.post(
            "/api/v1/telemetry",
            json={"invalid": "data"}
        )
        
        assert response.status_code == 422


class TestUtilityFunctions:
    """工具函数测试"""
    
    def test_assert_response_structure(self):
        """测试响应结构断言函数"""
        from tests.conftest import assert_response_structure
        
        # 有效结构
        data = {"key1": "value1", "key2": "value2"}
        assert_response_structure(data, ["key1", "key2"])
        
        # 缺少键
        with pytest.raises(AssertionError):
            assert_response_structure(data, ["key1", "key3"])
    
    def test_assert_error_response(self):
        """测试错误响应断言函数"""
        from tests.conftest import assert_error_response
        
        # 有效错误响应
        error_data = {
            "error": {
                "code": "TEST_ERROR",
                "message": "测试错误"
            }
        }
        assert_error_response(error_data, "TEST_ERROR")
        
        # 错误代码不匹配
        with pytest.raises(AssertionError):
            assert_error_response(error_data, "OTHER_ERROR")
        
        # 缺少错误字段
        with pytest.raises(AssertionError):
            assert_error_response({"invalid": "data"})