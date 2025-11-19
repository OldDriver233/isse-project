"""
Telemetry API 测试

测试用户反馈遥测数据收集的 API 端点。
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Telemetry
from tests.conftest import assert_response_structure, assert_error_response


class TestTelemetryEndpoint:
    """Telemetry API 端点测试"""

    def test_submit_feedback_success(
        self, client: TestClient, test_db: Session, sample_telemetry_request: dict
    ):
        """测试成功提交反馈"""
        response = client.post("/api/v1/telemetry", json=sample_telemetry_request)

        assert response.status_code == 200
        data = response.json()

        assert_response_structure(data, ["result"])
        assert data["result"] == "ok"

        # 验证数据库中的记录
        telemetry = test_db.query(Telemetry).first()
        assert telemetry is not None
        assert telemetry.user_id == sample_telemetry_request["user_id"]
        assert (
            telemetry.overall_rating == sample_telemetry_request["rating"]["overall_rating"]
        )
        assert telemetry.comment == sample_telemetry_request["rating"]["comment"]

    def test_submit_feedback_without_comment(
        self,
        client: TestClient,
        test_db: Session,
        sample_user_id: str,
        sample_messages: list,
    ):
        """测试提交没有评论的反馈"""
        request_data = {
            "user_id": sample_user_id,
            "rating": {"overall_rating": 7},
            "messages": sample_messages,
        }

        response = client.post("/api/v1/telemetry", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "ok"

        # 验证数据库
        telemetry = test_db.query(Telemetry).first()
        assert telemetry.comment is None

    def test_submit_feedback_invalid_rating_low(
        self, client: TestClient, sample_user_id: str, sample_messages: list
    ):
        """测试无效评分（过低）"""
        request_data = {
            "user_id": sample_user_id,
            "rating": {"overall_rating": 0},  # 小于最小值 1
            "messages": sample_messages,
        }

        response = client.post("/api/v1/telemetry", json=request_data)

        assert response.status_code == 422  # Validation error

    def test_submit_feedback_invalid_rating_high(
        self, client: TestClient, sample_user_id: str, sample_messages: list
    ):
        """测试无效评分（过高）"""
        request_data = {
            "user_id": sample_user_id,
            "rating": {"overall_rating": 11},  # 大于最大值 10
            "messages": sample_messages,
        }

        response = client.post("/api/v1/telemetry", json=request_data)

        assert response.status_code == 422  # Validation error

    def test_submit_feedback_missing_user_id(
        self, client: TestClient, sample_rating: dict, sample_messages: list
    ):
        """测试缺少用户 ID"""
        request_data = {"rating": sample_rating, "messages": sample_messages}

        response = client.post("/api/v1/telemetry", json=request_data)

        assert response.status_code == 422  # Validation error

    def test_submit_feedback_missing_rating(
        self, client: TestClient, sample_user_id: str, sample_messages: list
    ):
        """测试缺少评分"""
        request_data = {"user_id": sample_user_id, "messages": sample_messages}

        response = client.post("/api/v1/telemetry", json=request_data)

        assert response.status_code == 422  # Validation error

    def test_submit_feedback_empty_messages(
        self, client: TestClient, sample_user_id: str, sample_rating: dict
    ):
        """测试空消息列表"""
        request_data = {
            "user_id": sample_user_id,
            "rating": sample_rating,
            "messages": [],
        }

        response = client.post("/api/v1/telemetry", json=request_data)

        assert response.status_code == 422  # Validation error

    def test_submit_feedback_invalid_message_role(
        self, client: TestClient, sample_user_id: str, sample_rating: dict
    ):
        """测试无效的消息角色"""
        request_data = {
            "user_id": sample_user_id,
            "rating": sample_rating,
            "messages": [{"role": "invalid_role", "content": "测试内容"}],  # 无效角色
        }

        response = client.post("/api/v1/telemetry", json=request_data)

        assert response.status_code == 422  # Validation error

    def test_submit_multiple_feedback(
        self,
        client: TestClient,
        test_db: Session,
        sample_user_id: str,
        sample_messages: list,
    ):
        """测试提交多条反馈"""
        for rating in [5, 7, 9]:
            request_data = {
                "user_id": sample_user_id,
                "rating": {"overall_rating": rating, "comment": f"评分 {rating}"},
                "messages": sample_messages,
            }

            response = client.post("/api/v1/telemetry", json=request_data)
            assert response.status_code == 200

        # 验证数据库中有 3 条记录
        count = test_db.query(Telemetry).count()
        assert count == 3

    def test_submit_feedback_different_users(
        self,
        client: TestClient,
        test_db: Session,
        sample_rating: dict,
        sample_messages: list,
    ):
        """测试不同用户提交反馈"""
        user_ids = ["user-1", "user-2", "user-3"]

        for user_id in user_ids:
            request_data = {
                "user_id": user_id,
                "rating": sample_rating,
                "messages": sample_messages,
            }

            response = client.post("/api/v1/telemetry", json=request_data)
            assert response.status_code == 200

        # 验证每个用户都有记录
        for user_id in user_ids:
            telemetry = (
                test_db.query(Telemetry).filter(Telemetry.user_id == user_id).first()
            )
            assert telemetry is not None


class TestTelemetryStatsEndpoint:
    """Telemetry 统计 API 端点测试"""

    def test_get_stats_empty_database(self, client: TestClient):
        """测试空数据库的统计"""
        response = client.get("/api/v1/telemetry/stats")

        assert response.status_code == 200
        data = response.json()

        assert_response_structure(
            data, ["average_rating", "total_feedback", "rating_distribution"]
        )
        assert data["average_rating"] == 0.0
        assert data["total_feedback"] == 0
        assert data["rating_distribution"] == {}

    def test_get_stats_with_data(
        self, client: TestClient, test_db: Session, sample_messages: list
    ):
        """测试有数据时的统计"""
        # 创建测试数据
        ratings = [5, 7, 7, 8, 9, 10]
        for i, rating in enumerate(ratings):
            request_data = {
                "user_id": f"user-{i}",
                "rating": {"overall_rating": rating},
                "messages": sample_messages,
            }
            client.post("/api/v1/telemetry", json=request_data)

        # 获取统计
        response = client.get("/api/v1/telemetry/stats")

        assert response.status_code == 200
        data = response.json()

        # 验证平均评分
        expected_avg = sum(ratings) / len(ratings)
        assert abs(data["average_rating"] - expected_avg) < 0.01

        # 验证总数
        assert data["total_feedback"] == len(ratings)

        # 验证评分分布
        assert data["rating_distribution"]["7"] == 2  # 两个 7 分
        assert data["rating_distribution"]["5"] == 1
        assert data["rating_distribution"]["8"] == 1
        assert data["rating_distribution"]["9"] == 1
        assert data["rating_distribution"]["10"] == 1

    def test_get_stats_rating_distribution(
        self, client: TestClient, sample_messages: list
    ):
        """测试评分分布统计"""
        # 创建特定分布的数据
        rating_counts = {10: 5, 9: 3, 8: 2, 5: 1}

        user_id = 0
        for rating, count in rating_counts.items():
            for _ in range(count):
                request_data = {
                    "user_id": f"user-{user_id}",
                    "rating": {"overall_rating": rating},
                    "messages": sample_messages,
                }
                client.post("/api/v1/telemetry", json=request_data)
                user_id += 1

        # 获取统计
        response = client.get("/api/v1/telemetry/stats")
        data = response.json()

        # 验证分布
        for rating, expected_count in rating_counts.items():
            assert data["rating_distribution"][str(rating)] == expected_count

        # 验证总数
        total_expected = sum(rating_counts.values())
        assert data["total_feedback"] == total_expected


class TestTelemetryValidation:
    """Telemetry 数据验证测试"""

    def test_valid_rating_range(
        self, client: TestClient, sample_user_id: str, sample_messages: list
    ):
        """测试有效评分范围（1-10）"""
        for rating in range(1, 11):
            request_data = {
                "user_id": sample_user_id,
                "rating": {"overall_rating": rating},
                "messages": sample_messages,
            }

            response = client.post("/api/v1/telemetry", json=request_data)
            assert response.status_code == 200, f"评分 {rating} 应该有效"

    def test_message_roles_validation(
        self, client: TestClient, sample_user_id: str, sample_rating: dict
    ):
        """测试消息角色验证"""
        valid_roles = ["system", "user", "assistant"]

        for role in valid_roles:
            request_data = {
                "user_id": sample_user_id,
                "rating": sample_rating,
                "messages": [{"role": role, "content": f"测试 {role} 角色"}],
            }

            response = client.post("/api/v1/telemetry", json=request_data)
            assert response.status_code == 200, f"角色 {role} 应该有效"

    def test_long_comment(
        self, client: TestClient, sample_user_id: str, sample_messages: list
    ):
        """测试长评论"""
        long_comment = "这是一个很长的评论。" * 100  # 约 1000 字符

        request_data = {
            "user_id": sample_user_id,
            "rating": {"overall_rating": 8, "comment": long_comment},
            "messages": sample_messages,
        }

        response = client.post("/api/v1/telemetry", json=request_data)
        assert response.status_code == 200

    def test_special_characters_in_comment(
        self, client: TestClient, sample_user_id: str, sample_messages: list
    ):
        """测试评论中的特殊字符"""
        special_comment = "测试特殊字符: @#$%^&*()_+-=[]{}|;':\",./<>?`~"

        request_data = {
            "user_id": sample_user_id,
            "rating": {"overall_rating": 7, "comment": special_comment},
            "messages": sample_messages,
        }

        response = client.post("/api/v1/telemetry", json=request_data)
        assert response.status_code == 200

    def test_unicode_in_messages(
        self, client: TestClient, sample_user_id: str, sample_rating: dict
    ):
        """测试消息中的 Unicode 字符"""
        unicode_messages = [
            {"role": "user", "content": "你好世界 🌍 こんにちは مرحبا"},
            {"role": "assistant", "content": "回复包含表情符号 😊 和各种语言"},
        ]

        request_data = {
            "user_id": sample_user_id,
            "rating": sample_rating,
            "messages": unicode_messages,
        }

        response = client.post("/api/v1/telemetry", json=request_data)
        assert response.status_code == 200
