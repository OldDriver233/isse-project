"""
服务层测试

测试业务逻辑服务层的功能。
"""

import pytest
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.telemetry_service import TelemetryService
from app.models import Telemetry
from app.schemas import Rating, Message


class TestTelemetryService:
    """TelemetryService 测试"""

    @pytest.mark.asyncio
    async def test_save_feedback_success(
        self,
        test_db: Session,
        sample_user_id: str,
        sample_rating: dict,
        sample_messages: list,
    ):
        """测试成功保存反馈"""
        service = TelemetryService(test_db)

        rating = Rating(**sample_rating)
        messages = [Message(**msg) for msg in sample_messages]

        result = await service.save_feedback(
            user_id=sample_user_id, rating=rating, messages=messages
        )

        assert result is True

        # 验证数据库记录
        telemetry = test_db.query(Telemetry).first()
        assert telemetry is not None
        assert telemetry.user_id == sample_user_id
        assert telemetry.overall_rating == sample_rating["overall_rating"]
        assert telemetry.comment == sample_rating["comment"]

        # 验证消息 JSON
        saved_messages = json.loads(telemetry.messages)
        assert len(saved_messages) == len(sample_messages)
        assert saved_messages[0]["role"] == sample_messages[0]["role"]
        assert saved_messages[0]["content"] == sample_messages[0]["content"]

    @pytest.mark.asyncio
    async def test_save_feedback_without_comment(
        self, test_db: Session, sample_user_id: str, sample_messages: list
    ):
        """测试保存没有评论的反馈"""
        service = TelemetryService(test_db)

        rating = Rating(overall_rating=7, comment=None)
        messages = [Message(**msg) for msg in sample_messages]

        result = await service.save_feedback(
            user_id=sample_user_id, rating=rating, messages=messages
        )

        assert result is True

        telemetry = test_db.query(Telemetry).first()
        assert telemetry.comment is None

    @pytest.mark.asyncio
    async def test_save_multiple_feedback(
        self, test_db: Session, sample_user_id: str, sample_messages: list
    ):
        """测试保存多条反馈"""
        service = TelemetryService(test_db)
        messages = [Message(**msg) for msg in sample_messages]

        for rating_value in [5, 7, 9]:
            rating = Rating(overall_rating=rating_value, comment=f"评分 {rating_value}")
            result = await service.save_feedback(
                user_id=sample_user_id, rating=rating, messages=messages
            )
            assert result is True

        # 验证数据库中有 3 条记录
        count = test_db.query(Telemetry).count()
        assert count == 3

    @pytest.mark.asyncio
    async def test_get_user_feedback(
        self, test_db: Session, sample_user_id: str, sample_messages: list
    ):
        """测试查询用户反馈"""
        service = TelemetryService(test_db)
        messages = [Message(**msg) for msg in sample_messages]

        # 创建测试数据
        for i in range(5):
            rating = Rating(overall_rating=5 + i, comment=f"反馈 {i}")
            await service.save_feedback(
                user_id=sample_user_id, rating=rating, messages=messages
            )

        # 查询反馈
        feedback_list = await service.get_user_feedback(user_id=sample_user_id, limit=3)

        assert len(feedback_list) == 3
        # 应该按创建时间倒序排列
        assert feedback_list[0].overall_rating >= feedback_list[1].overall_rating

    @pytest.mark.asyncio
    async def test_get_user_feedback_empty(self, test_db: Session):
        """测试查询不存在的用户反馈"""
        service = TelemetryService(test_db)

        feedback_list = await service.get_user_feedback(
            user_id="non-existent-user", limit=10
        )

        assert len(feedback_list) == 0

    @pytest.mark.asyncio
    async def test_get_recent_feedback(self, test_db: Session, sample_messages: list):
        """测试查询最近的反馈"""
        service = TelemetryService(test_db)
        messages = [Message(**msg) for msg in sample_messages]

        # 创建不同用户的反馈
        for i in range(10):
            rating = Rating(overall_rating=5, comment=f"用户 {i}")
            await service.save_feedback(
                user_id=f"user-{i}", rating=rating, messages=messages
            )

        # 查询最近 5 条
        recent_feedback = await service.get_recent_feedback(limit=5)

        assert len(recent_feedback) == 5

    @pytest.mark.asyncio
    async def test_get_average_rating_empty(self, test_db: Session):
        """测试空数据库的平均评分"""
        service = TelemetryService(test_db)

        avg_rating = await service.get_average_rating()

        assert avg_rating == 0.0

    @pytest.mark.asyncio
    async def test_get_average_rating_with_data(
        self, test_db: Session, sample_user_id: str, sample_messages: list
    ):
        """测试计算平均评分"""
        service = TelemetryService(test_db)
        messages = [Message(**msg) for msg in sample_messages]

        ratings = [5, 7, 8, 9, 10]
        for rating_value in ratings:
            rating = Rating(overall_rating=rating_value)
            await service.save_feedback(
                user_id=sample_user_id, rating=rating, messages=messages
            )

        avg_rating = await service.get_average_rating()
        expected_avg = sum(ratings) / len(ratings)

        assert abs(avg_rating - expected_avg) < 0.01

    @pytest.mark.asyncio
    async def test_get_average_rating_with_days_filter(
        self, test_db: Session, sample_user_id: str, sample_messages: list
    ):
        """测试带时间过滤的平均评分"""
        service = TelemetryService(test_db)
        messages = [Message(**msg) for msg in sample_messages]

        # 创建一些反馈
        rating = Rating(overall_rating=8)
        await service.save_feedback(
            user_id=sample_user_id, rating=rating, messages=messages
        )

        # 查询最近 7 天的平均评分
        avg_rating = await service.get_average_rating(days=7)

        assert avg_rating == 8.0

    @pytest.mark.asyncio
    async def test_get_rating_distribution_empty(self, test_db: Session):
        """测试空数据库的评分分布"""
        service = TelemetryService(test_db)

        distribution = await service.get_rating_distribution()

        assert distribution == {}

    @pytest.mark.asyncio
    async def test_get_rating_distribution_with_data(
        self, test_db: Session, sample_user_id: str, sample_messages: list
    ):
        """测试评分分布统计"""
        service = TelemetryService(test_db)
        messages = [Message(**msg) for msg in sample_messages]

        # 创建特定分布的数据
        rating_counts = {10: 5, 9: 3, 8: 2, 5: 1}

        user_id = 0
        for rating_value, count in rating_counts.items():
            for _ in range(count):
                rating = Rating(overall_rating=rating_value)
                await service.save_feedback(
                    user_id=f"user-{user_id}", rating=rating, messages=messages
                )
                user_id += 1

        distribution = await service.get_rating_distribution()

        # 验证分布
        for rating_value, expected_count in rating_counts.items():
            assert distribution[rating_value] == expected_count

    @pytest.mark.asyncio
    async def test_get_low_rating_feedback(
        self, test_db: Session, sample_messages: list
    ):
        """测试查询低评分反馈"""
        service = TelemetryService(test_db)
        messages = [Message(**msg) for msg in sample_messages]

        # 创建不同评分的反馈
        ratings = [3, 4, 5, 7, 8, 9]
        for i, rating_value in enumerate(ratings):
            rating = Rating(overall_rating=rating_value, comment=f"评分 {rating_value}")
            await service.save_feedback(
                user_id=f"user-{i}", rating=rating, messages=messages
            )

        # 查询评分 <= 5 的反馈
        low_ratings = await service.get_low_rating_feedback(threshold=5, limit=10)

        assert len(low_ratings) == 3
        assert all(r.overall_rating <= 5 for r in low_ratings)

    @pytest.mark.asyncio
    async def test_get_low_rating_feedback_with_limit(
        self, test_db: Session, sample_messages: list
    ):
        """测试带限制的低评分查询"""
        service = TelemetryService(test_db)
        messages = [Message(**msg) for msg in sample_messages]

        # 创建 5 条低评分反馈
        for i in range(5):
            rating = Rating(overall_rating=3)
            await service.save_feedback(
                user_id=f"user-{i}", rating=rating, messages=messages
            )

        # 只查询 2 条
        low_ratings = await service.get_low_rating_feedback(threshold=5, limit=2)

        assert len(low_ratings) == 2

    @pytest.mark.asyncio
    async def test_cleanup_old_data(
        self, test_db: Session, sample_user_id: str, sample_messages: list
    ):
        """测试清理旧数据"""
        service = TelemetryService(test_db)
        messages = [Message(**msg) for msg in sample_messages]

        # 创建一些反馈
        rating = Rating(overall_rating=8)
        for i in range(5):
            await service.save_feedback(
                user_id=f"user-{i}", rating=rating, messages=messages
            )

        # 模拟清理 90 天前的数据（实际上这些数据都是新的，所以不会被删除）
        deleted_count = await service.cleanup_old_data(days=90)

        # 由于数据都是刚创建的，不应该被删除
        assert deleted_count == 0

        # 验证数据仍然存在
        remaining_count = test_db.query(Telemetry).count()
        assert remaining_count == 5

    @pytest.mark.asyncio
    async def test_save_feedback_with_special_characters(
        self, test_db: Session, sample_user_id: str
    ):
        """测试保存包含特殊字符的反馈"""
        service = TelemetryService(test_db)

        rating = Rating(
            overall_rating=8, comment="特殊字符测试: @#$%^&*()_+-=[]{}|;':\",./<>?`~"
        )
        messages = [
            Message(role="user", content="包含表情符号 😊 🎉 ❤️"),
            Message(role="assistant", content="多语言测试: 你好 こんにちは مرحبا"),
        ]

        result = await service.save_feedback(
            user_id=sample_user_id, rating=rating, messages=messages
        )

        assert result is True

        # 验证数据正确保存
        telemetry = test_db.query(Telemetry).first()
        assert telemetry.comment == rating.comment

        saved_messages = json.loads(telemetry.messages)
        assert "😊" in saved_messages[0]["content"]
        assert "こんにちは" in saved_messages[1]["content"]

    @pytest.mark.asyncio
    async def test_save_feedback_with_long_content(
        self, test_db: Session, sample_user_id: str
    ):
        """测试保存长内容"""
        service = TelemetryService(test_db)

        long_comment = "这是一个很长的评论。" * 200  # 约 2000 字符
        long_message = "这是一个很长的消息。" * 500  # 约 5000 字符

        rating = Rating(overall_rating=7, comment=long_comment)
        messages = [
            Message(role="user", content=long_message),
            Message(role="assistant", content=long_message),
        ]

        result = await service.save_feedback(
            user_id=sample_user_id, rating=rating, messages=messages
        )

        assert result is True

        # 验证数据完整性
        telemetry = test_db.query(Telemetry).first()
        assert len(telemetry.comment) > 1000

        saved_messages = json.loads(telemetry.messages)
        assert len(saved_messages[0]["content"]) > 1000
