"""
集成测试

测试多个组件协同工作的端到端场景。
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Telemetry


class TestEndToEndChatFlow:
    """端到端对话流程测试"""

    @patch("app.services.ai_service.ai_service.chat")
    def test_complete_chat_and_feedback_flow(
        self,
        mock_chat: AsyncMock,
        client: TestClient,
        test_db: Session,
        mock_ai_response: dict,
    ):
        """测试完整的对话和反馈流程"""
        mock_chat.return_value = mock_ai_response

        # 1. 用户发起对话
        chat_request = {
            "character": "tocqueville",
            "messages": [{"role": "user", "content": "请介绍一下美国民主"}],
            "stream": False,
            "temperature": 0.5,
        }

        chat_response = client.post("/api/v1/chat", json=chat_request)
        assert chat_response.status_code == 200

        chat_data = chat_response.json()
        assistant_message = chat_data["result"]["message"]

        # 2. 用户提交反馈
        telemetry_request = {
            "user_id": "test-user-e2e",
            "rating": {"overall_rating": 9, "comment": "回答很详细"},
            "messages": [
                {"role": "user", "content": "请介绍一下美国民主"},
                assistant_message,
            ],
        }

        telemetry_response = client.post("/api/v1/telemetry", json=telemetry_request)
        assert telemetry_response.status_code == 200
        assert telemetry_response.json()["result"] == "ok"

        # 3. 验证反馈已保存到数据库
        feedback = (
            test_db.query(Telemetry)
            .filter(Telemetry.user_id == "test-user-e2e")
            .first()
        )

        assert feedback is not None
        assert feedback.overall_rating == 9
        assert feedback.comment == "回答很详细"

    @patch("app.services.ai_service.ai_service.chat")
    def test_multiple_conversations_with_feedback(
        self,
        mock_chat: AsyncMock,
        client: TestClient,
        test_db: Session,
        mock_ai_response: dict,
    ):
        """测试多轮对话和反馈"""
        mock_chat.return_value = mock_ai_response

        user_id = "test-user-multi"
        conversation_history = []

        # 进行 3 轮对话
        questions = ["什么是民主？", "美国民主有什么特点？", "民主制度的优缺点是什么？"]

        for question in questions:
            # 添加用户消息
            conversation_history.append({"role": "user", "content": question})

            # 发送对话请求
            chat_request = {
                "character": "tocqueville",
                "messages": conversation_history.copy(),
                "stream": False,
            }

            response = client.post("/api/v1/chat", json=chat_request)
            assert response.status_code == 200

            # 添加助手回复
            assistant_message = response.json()["result"]["message"]
            conversation_history.append(assistant_message)

        # 提交整个对话的反馈
        telemetry_request = {
            "user_id": user_id,
            "rating": {"overall_rating": 8, "comment": "多轮对话很流畅"},
            "messages": conversation_history,
        }

        response = client.post("/api/v1/telemetry", json=telemetry_request)
        assert response.status_code == 200

        # 验证反馈
        feedback = test_db.query(Telemetry).filter(Telemetry.user_id == user_id).first()

        assert feedback is not None
        assert len(conversation_history) == 6  # 3 轮对话，每轮 2 条消息


class TestMultiUserScenarios:
    """多用户场景测试"""

    @patch("app.services.ai_service.ai_service.chat")
    def test_concurrent_users_chat(
        self, mock_chat: AsyncMock, client: TestClient, mock_ai_response: dict
    ):
        """测试并发用户对话"""
        mock_chat.return_value = mock_ai_response

        # 模拟 5 个用户同时发起对话
        users = [f"user-{i}" for i in range(5)]

        for user_id in users:
            chat_request = {
                "character": "tocqueville",
                "messages": [{"role": "user", "content": f"来自 {user_id} 的问题"}],
                "stream": False,
            }

            response = client.post("/api/v1/chat", json=chat_request)
            assert response.status_code == 200

    def test_multiple_users_feedback(
        self, client: TestClient, test_db: Session, sample_messages: list
    ):
        """测试多用户提交反馈"""
        # 5 个用户提交不同评分的反馈
        ratings = [5, 6, 7, 8, 9]

        for i, rating in enumerate(ratings):
            telemetry_request = {
                "user_id": f"user-{i}",
                "rating": {"overall_rating": rating, "comment": f"评分 {rating}"},
                "messages": sample_messages,
            }

            response = client.post("/api/v1/telemetry", json=telemetry_request)
            assert response.status_code == 200

        # 验证统计数据
        stats_response = client.get("/api/v1/telemetry/stats")
        assert stats_response.status_code == 200

        stats = stats_response.json()
        assert stats["total_feedback"] == 5

        # 平均评分应该是 7
        expected_avg = sum(ratings) / len(ratings)
        assert abs(stats["average_rating"] - expected_avg) < 0.01


class TestErrorRecovery:
    """错误恢复测试"""

    @patch("app.services.ai_service.ai_service.chat")
    def test_chat_failure_then_success(
        self,
        mock_chat: AsyncMock,
        client: TestClient,
        sample_chat_request: dict,
        mock_ai_response: dict,
    ):
        """测试对话失败后重试成功"""
        # 第一次调用失败
        mock_chat.side_effect = [
            ConnectionError("服务暂时不可用"),
            mock_ai_response,  # 第二次成功
        ]

        # 第一次请求失败
        response1 = client.post("/api/v1/chat", json=sample_chat_request)
        assert response1.status_code == 503

        # 重置 mock
        mock_chat.side_effect = None
        mock_chat.return_value = mock_ai_response

        # 第二次请求成功
        response2 = client.post("/api/v1/chat", json=sample_chat_request)
        assert response2.status_code == 200

    def test_feedback_submission_retry(
        self, client: TestClient, test_db: Session, sample_telemetry_request: dict
    ):
        """测试反馈提交重试"""
        # 第一次提交
        response1 = client.post("/api/v1/telemetry", json=sample_telemetry_request)
        assert response1.status_code == 200

        # 修改评分后再次提交（同一用户）
        sample_telemetry_request["rating"]["overall_rating"] = 10
        sample_telemetry_request["rating"]["comment"] = "更新后的评价"

        response2 = client.post("/api/v1/telemetry", json=sample_telemetry_request)
        assert response2.status_code == 200

        # 验证数据库中有 2 条记录
        count = (
            test_db.query(Telemetry)
            .filter(Telemetry.user_id == sample_telemetry_request["user_id"])
            .count()
        )

        assert count == 2


class TestDataConsistency:
    """数据一致性测试"""

    def test_feedback_data_integrity(
        self, client: TestClient, test_db: Session, sample_user_id: str
    ):
        """测试反馈数据完整性"""
        # 提交包含特殊字符的反馈
        special_messages = [
            {"role": "user", "content": "测试特殊字符: @#$%^&*() 中文 😊 🎉"},
            {
                "role": "assistant",
                "content": '回复包含 JSON 特殊字符: {"key": "value"}, [1, 2, 3]',
            },
        ]

        telemetry_request = {
            "user_id": sample_user_id,
            "rating": {
                "overall_rating": 8,
                "comment": "包含引号的评论: \"很好\" '不错'",
            },
            "messages": special_messages,
        }

        response = client.post("/api/v1/telemetry", json=telemetry_request)
        assert response.status_code == 200

        # 验证数据正确保存
        feedback = (
            test_db.query(Telemetry).filter(Telemetry.user_id == sample_user_id).first()
        )

        assert feedback is not None
        assert "😊" in feedback.messages
        assert '"很好"' in feedback.comment

    def test_statistics_accuracy(
        self, client: TestClient, test_db: Session, sample_messages: list
    ):
        """测试统计数据准确性"""
        # 创建已知分布的数据
        rating_distribution = {10: 3, 8: 5, 6: 2, 4: 1}

        user_id = 0
        for rating, count in rating_distribution.items():
            for _ in range(count):
                telemetry_request = {
                    "user_id": f"user-{user_id}",
                    "rating": {"overall_rating": rating},
                    "messages": sample_messages,
                }

                response = client.post("/api/v1/telemetry", json=telemetry_request)
                assert response.status_code == 200
                user_id += 1

        # 获取统计数据
        stats_response = client.get("/api/v1/telemetry/stats")
        stats = stats_response.json()

        # 验证总数
        expected_total = sum(rating_distribution.values())
        assert stats["total_feedback"] == expected_total

        # 验证分布
        for rating, expected_count in rating_distribution.items():
            assert stats["rating_distribution"][rating] == expected_count

        # 验证平均值
        total_score = sum(
            rating * count for rating, count in rating_distribution.items()
        )
        expected_avg = total_score / expected_total
        assert abs(stats["average_rating"] - expected_avg) < 0.01


class TestAPIWorkflow:
    """API 工作流测试"""

    def test_health_check_before_operations(self, client: TestClient):
        """测试操作前的健康检查"""
        # 先检查服务健康状态
        health_response = client.get("/health")
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "healthy"

        # 然后进行正常操作
        root_response = client.get("/")
        assert root_response.status_code == 200

    @patch("app.services.ai_service.ai_service.chat")
    def test_complete_user_journey(
        self,
        mock_chat: AsyncMock,
        client: TestClient,
        test_db: Session,
        mock_ai_response: dict,
    ):
        """测试完整的用户旅程"""
        mock_chat.return_value = mock_ai_response

        user_id = "journey-user"

        # 1. 检查服务状态
        health = client.get("/health")
        assert health.status_code == 200

        # 2. 查看 API 文档（根路径）
        root = client.get("/")
        assert root.status_code == 200
        assert "docs" in root.json()

        # 3. 开始对话
        chat_response = client.post(
            "/api/v1/chat",
            json={
                "character": "tocqueville",
                "messages": [{"role": "user", "content": "你好"}],
                "stream": False,
            },
        )
        assert chat_response.status_code == 200

        # 4. 继续对话
        messages = [
            {"role": "user", "content": "你好"},
            chat_response.json()["result"]["message"],
            {"role": "user", "content": "继续"},
        ]

        chat_response2 = client.post(
            "/api/v1/chat",
            json={"character": "tocqueville", "messages": messages, "stream": False},
        )
        assert chat_response2.status_code == 200

        # 5. 提交反馈
        messages.append(chat_response2.json()["result"]["message"])

        feedback_response = client.post(
            "/api/v1/telemetry",
            json={
                "user_id": user_id,
                "rating": {"overall_rating": 9, "comment": "很好的体验"},
                "messages": messages,
            },
        )
        assert feedback_response.status_code == 200

        # 6. 查看统计（可选）
        stats_response = client.get("/api/v1/telemetry/stats")
        assert stats_response.status_code == 200
        assert stats_response.json()["total_feedback"] >= 1


class TestEdgeCases:
    """边界情况测试"""

    @patch("app.services.ai_service.ai_service.chat")
    def test_very_long_conversation(
        self, mock_chat: AsyncMock, client: TestClient, mock_ai_response: dict
    ):
        """测试非常长的对话"""
        mock_chat.return_value = mock_ai_response

        # 创建 20 轮对话
        messages = []
        for i in range(20):
            messages.append({"role": "user", "content": f"问题 {i}"})
            messages.append({"role": "assistant", "content": f"回答 {i}"})

        messages.append({"role": "user", "content": "最后一个问题"})

        chat_request = {
            "character": "tocqueville",
            "messages": messages,
            "stream": False,
        }

        response = client.post("/api/v1/chat", json=chat_request)
        assert response.status_code == 200

    def test_rapid_feedback_submissions(
        self,
        client: TestClient,
        test_db: Session,
        sample_user_id: str,
        sample_messages: list,
    ):
        """测试快速连续提交反馈"""
        # 快速提交 10 条反馈
        for i in range(10):
            telemetry_request = {
                "user_id": sample_user_id,
                "rating": {"overall_rating": (i % 10) + 1},
                "messages": sample_messages,
            }

            response = client.post("/api/v1/telemetry", json=telemetry_request)
            assert response.status_code == 200

        # 验证所有反馈都已保存
        count = (
            test_db.query(Telemetry).filter(Telemetry.user_id == sample_user_id).count()
        )

        assert count == 10
