"""
Chat API 测试

测试与 AI 智能体对话交互的 API 端点。
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from tests.conftest import assert_response_structure, assert_error_response


class TestChatEndpoint:
    """Chat API 端点测试"""
    
    @patch('app.services.ai_service.ai_service.chat')
    def test_chat_success_non_stream(
        self,
        mock_chat: AsyncMock,
        client: TestClient,
        sample_chat_request: dict,
        mock_ai_response: dict
    ):
        """测试成功的非流式对话"""
        mock_chat.return_value = mock_ai_response
        
        response = client.post("/api/v1/chat", json=sample_chat_request)
        
        assert response.status_code == 200
        data = response.json()
        
        # 验证响应结构
        assert_response_structure(data, ["result", "usage", "created", "id"])
        assert_response_structure(data["result"], ["message", "finish_reason"])
        assert_response_structure(data["result"]["message"], ["role", "content"])
        assert_response_structure(data["usage"], ["prompt_tokens", "completion_tokens", "total_tokens"])
        
        # 验证内容
        assert data["result"]["message"]["role"] == "assistant"
        assert len(data["result"]["message"]["content"]) > 0
        assert data["result"]["finish_reason"] == "stop"
    
    @patch('app.services.ai_service.ai_service.chat')
    def test_chat_with_temperature(
        self,
        mock_chat: AsyncMock,
        client: TestClient,
        mock_ai_response: dict
    ):
        """测试带温度参数的对话"""
        mock_chat.return_value = mock_ai_response
        
        request_data = {
            "character": "tocqueville",
            "messages": [
                {"role": "user", "content": "测试"}
            ],
            "stream": False,
            "temperature": 0.8
        }
        
        response = client.post("/api/v1/chat", json=request_data)
        
        assert response.status_code == 200
        
        # 验证调用参数
        mock_chat.assert_called_once()
        call_args = mock_chat.call_args
        assert call_args.kwargs["temperature"] == 0.8
    
    @patch('app.services.ai_service.ai_service.chat')
    def test_chat_invalid_character(
        self,
        mock_chat: AsyncMock,
        client: TestClient
    ):
        """测试无效的角色名称"""
        mock_chat.side_effect = KeyError("角色不存在")
        
        request_data = {
            "character": "invalid_character",
            "messages": [
                {"role": "user", "content": "测试"}
            ],
            "stream": False
        }
        
        response = client.post("/api/v1/chat", json=request_data)
        
        assert response.status_code == 404
        data = response.json()
        assert_error_response(data, "CHARACTER_NOT_FOUND")
    
    def test_chat_missing_character(self, client: TestClient):
        """测试缺少角色参数"""
        request_data = {
            "messages": [
                {"role": "user", "content": "测试"}
            ],
            "stream": False
        }
        
        response = client.post("/api/v1/chat", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_chat_empty_messages(self, client: TestClient):
        """测试空消息列表"""
        request_data = {
            "character": "tocqueville",
            "messages": [],
            "stream": False
        }
        
        response = client.post("/api/v1/chat", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_chat_invalid_message_role(self, client: TestClient):
        """测试无效的消息角色"""
        request_data = {
            "character": "tocqueville",
            "messages": [
                {"role": "invalid_role", "content": "测试"}
            ],
            "stream": False
        }
        
        response = client.post("/api/v1/chat", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_chat_temperature_out_of_range_low(self, client: TestClient):
        """测试温度参数过低"""
        request_data = {
            "character": "tocqueville",
            "messages": [
                {"role": "user", "content": "测试"}
            ],
            "stream": False,
            "temperature": -0.1  # 小于最小值 0.0
        }
        
        response = client.post("/api/v1/chat", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_chat_temperature_out_of_range_high(self, client: TestClient):
        """测试温度参数过高"""
        request_data = {
            "character": "tocqueville",
            "messages": [
                {"role": "user", "content": "测试"}
            ],
            "stream": False,
            "temperature": 2.1  # 大于最大值 2.0
        }
        
        response = client.post("/api/v1/chat", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    @patch('app.services.ai_service.ai_service.chat')
    def test_chat_with_conversation_history(
        self,
        mock_chat: AsyncMock,
        client: TestClient,
        mock_ai_response: dict
    ):
        """测试带对话历史的请求"""
        mock_chat.return_value = mock_ai_response
        
        request_data = {
            "character": "tocqueville",
            "messages": [
                {"role": "user", "content": "第一个问题"},
                {"role": "assistant", "content": "第一个回答"},
                {"role": "user", "content": "第二个问题"}
            ],
            "stream": False
        }
        
        response = client.post("/api/v1/chat", json=request_data)
        
        assert response.status_code == 200
        
        # 验证传递了完整的对话历史
        call_args = mock_chat.call_args
        assert len(call_args.kwargs["messages"]) == 3
    
    @patch('app.services.ai_service.ai_service.chat')
    def test_chat_ai_service_unavailable(
        self,
        mock_chat: AsyncMock,
        client: TestClient,
        sample_chat_request: dict
    ):
        """测试 AI 服务不可用"""
        mock_chat.side_effect = ConnectionError("AI 服务连接失败")
        
        response = client.post("/api/v1/chat", json=sample_chat_request)
        
        assert response.status_code == 503
        data = response.json()
        assert_error_response(data, "AI_SERVICE_UNAVAILABLE")
    
    @patch('app.services.ai_service.ai_service.chat')
    def test_chat_internal_error(
        self,
        mock_chat: AsyncMock,
        client: TestClient,
        sample_chat_request: dict
    ):
        """测试内部错误"""
        mock_chat.side_effect = Exception("未知错误")
        
        response = client.post("/api/v1/chat", json=sample_chat_request)
        
        assert response.status_code == 500
        data = response.json()
        assert_error_response(data, "INTERNAL_ERROR")


class TestChatStreamingEndpoint:
    """Chat 流式响应测试"""
    
    @patch('app.services.ai_service.ai_service.chat')
    def test_chat_stream_request(
        self,
        mock_chat: AsyncMock,
        client: TestClient
    ):
        """测试流式请求"""
        # Mock 流式生成器
        async def mock_stream():
            chunks = [
                'data: {"result":{"delta":{"role":"assistant","content":"你好"}}}\n\n',
                'data: {"result":{"delta":{"content":"，"}}}\n\n',
                'data: {"result":{"delta":{"content":"世界"}}}\n\n',
                'data: [DONE]\n\n'
            ]
            for chunk in chunks:
                yield chunk
        
        mock_chat.return_value = mock_stream()
        
        request_data = {
            "character": "tocqueville",
            "messages": [
                {"role": "user", "content": "你好"}
            ],
            "stream": True
        }
        
        response = client.post("/api/v1/chat", json=request_data)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    
    @patch('app.services.ai_service.ai_service.chat')
    def test_chat_stream_parameter(
        self,
        mock_chat: AsyncMock,
        client: TestClient,
        mock_ai_response: dict
    ):
        """测试 stream 参数传递"""
        mock_chat.return_value = mock_ai_response
        
        # 测试 stream=False
        request_data = {
            "character": "tocqueville",
            "messages": [{"role": "user", "content": "测试"}],
            "stream": False
        }
        
        response = client.post("/api/v1/chat", json=request_data)
        assert response.status_code == 200
        
        call_args = mock_chat.call_args
        assert call_args.kwargs["stream"] is False


class TestChatValidation:
    """Chat 数据验证测试"""
    
    @patch('app.services.ai_service.ai_service.chat')
    def test_valid_message_roles(
        self,
        mock_chat: AsyncMock,
        client: TestClient,
        mock_ai_response: dict
    ):
        """测试有效的消息角色"""
        mock_chat.return_value = mock_ai_response
        
        valid_roles = ["system", "user", "assistant"]
        
        for role in valid_roles:
            request_data = {
                "character": "tocqueville",
                "messages": [
                    {"role": role, "content": f"测试 {role} 角色"}
                ],
                "stream": False
            }
            
            response = client.post("/api/v1/chat", json=request_data)
            assert response.status_code == 200, f"角色 {role} 应该有效"
    
    @patch('app.services.ai_service.ai_service.chat')
    def test_character_case_insensitive(
        self,
        mock_chat: AsyncMock,
        client: TestClient,
        mock_ai_response: dict
    ):
        """测试角色名称大小写不敏感"""
        mock_chat.return_value = mock_ai_response
        
        character_variations = ["tocqueville", "Tocqueville", "TOCQUEVILLE", "ToCqUeViLlE"]
        
        for character in character_variations:
            request_data = {
                "character": character,
                "messages": [{"role": "user", "content": "测试"}],
                "stream": False
            }
            
            response = client.post("/api/v1/chat", json=request_data)
            # 应该都被规范化为小写
            call_args = mock_chat.call_args
            assert call_args.kwargs["character"] == "tocqueville"
    
    @patch('app.services.ai_service.ai_service.chat')
    def test_long_message_content(
        self,
        mock_chat: AsyncMock,
        client: TestClient,
        mock_ai_response: dict
    ):
        """测试长消息内容"""
        mock_chat.return_value = mock_ai_response
        
        long_content = "这是一个很长的消息。" * 500  # 约 5000 字符
        
        request_data = {
            "character": "tocqueville",
            "messages": [
                {"role": "user", "content": long_content}
            ],
            "stream": False
        }
        
        response = client.post("/api/v1/chat", json=request_data)
        assert response.status_code == 200
    
    @patch('app.services.ai_service.ai_service.chat')
    def test_unicode_in_messages(
        self,
        mock_chat: AsyncMock,
        client: TestClient,
        mock_ai_response: dict
    ):
        """测试消息中的 Unicode 字符"""
        mock_chat.return_value = mock_ai_response
        
        unicode_content = "你好世界 🌍 こんにちは مرحبا Привет"
        
        request_data = {
            "character": "tocqueville",
            "messages": [
                {"role": "user", "content": unicode_content}
            ],
            "stream": False
        }
        
        response = client.post("/api/v1/chat", json=request_data)
        assert response.status_code == 200
    
    @patch('app.services.ai_service.ai_service.chat')
    def test_multiple_messages_in_conversation(
        self,
        mock_chat: AsyncMock,
        client: TestClient,
        mock_ai_response: dict
    ):
        """测试多轮对话"""
        mock_chat.return_value = mock_ai_response
        
        messages = []
        for i in range(10):
            messages.append({"role": "user", "content": f"问题 {i}"})
            messages.append({"role": "assistant", "content": f"回答 {i}"})
        
        messages.append({"role": "user", "content": "最后一个问题"})
        
        request_data = {
            "character": "tocqueville",
            "messages": messages,
            "stream": False
        }
        
        response = client.post("/api/v1/chat", json=request_data)
        assert response.status_code == 200


class TestChatErrorHandling:
    """Chat 错误处理测试"""
    
    @patch('app.services.ai_service.ai_service.chat')
    def test_value_error_handling(
        self,
        mock_chat: AsyncMock,
        client: TestClient,
        sample_chat_request: dict
    ):
        """测试 ValueError 处理"""
        mock_chat.side_effect = ValueError("参数验证失败")
        
        response = client.post("/api/v1/chat", json=sample_chat_request)
        
        assert response.status_code == 400
        data = response.json()
        assert_error_response(data, "INVALID_REQUEST")
    
    @patch('app.services.ai_service.ai_service.chat')
    def test_key_error_handling(
        self,
        mock_chat: AsyncMock,
        client: TestClient,
        sample_chat_request: dict
    ):
        """测试 KeyError 处理（角色不存在）"""
        mock_chat.side_effect = KeyError("角色不存在")
        
        response = client.post("/api/v1/chat", json=sample_chat_request)
        
        assert response.status_code == 404
        data = response.json()
        assert_error_response(data, "CHARACTER_NOT_FOUND")
    
    @patch('app.services.ai_service.ai_service.chat')
    def test_connection_error_handling(
        self,
        mock_chat: AsyncMock,
        client: TestClient,
        sample_chat_request: dict
    ):
        """测试 ConnectionError 处理"""
        mock_chat.side_effect = ConnectionError("无法连接到 AI 服务")
        
        response = client.post("/api/v1/chat", json=sample_chat_request)
        
        assert response.status_code == 503
        data = response.json()
        assert_error_response(data, "AI_SERVICE_UNAVAILABLE")