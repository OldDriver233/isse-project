"""
遥测服务模块

处理用户反馈数据的存储和查询。
"""

import json
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models import Telemetry
from app.schemas import Rating, Message


class TelemetryService:
    """
    遥测服务类

    提供用户反馈数据的存储、查询和统计功能。
    """

    def __init__(self, db: Session):
        """
        初始化遥测服务

        Args:
            db: 数据库会话
        """
        self.db = db

    async def save_feedback(
        self, user_id: str, rating: Rating, messages: List[Message]
    ) -> bool:
        """
        保存用户反馈到数据库

        Args:
            user_id: 用户 UUID
            rating: 用户评分
            messages: 对话消息记录

        Returns:
            是否保存成功
        """
        try:
            # 将消息列表转换为 JSON 字符串
            messages_json = json.dumps(
                [msg.model_dump() for msg in messages], ensure_ascii=False
            )

            # 创建遥测记录
            telemetry = Telemetry(
                user_id=user_id,
                overall_rating=rating.overall_rating,
                comment=rating.comment,
                messages=messages_json,
            )

            # 保存到数据库
            self.db.add(telemetry)
            self.db.commit()
            self.db.refresh(telemetry)

            print(
                f"✅ 用户反馈已保存: user_id={user_id}, rating={rating.overall_rating}"
            )
            return True

        except Exception as e:
            print(f"❌ 保存用户反馈失败: {e}")
            self.db.rollback()
            raise

    async def get_user_feedback(self, user_id: str, limit: int = 10) -> List[Telemetry]:
        """
        查询用户的历史反馈

        Args:
            user_id: 用户 UUID
            limit: 返回数量限制

        Returns:
            遥测记录列表
        """
        try:
            return (
                self.db.query(Telemetry)
                .filter(Telemetry.user_id == user_id)
                .order_by(Telemetry.created_at.desc())
                .limit(limit)
                .all()
            )
        except Exception as e:
            print(f"❌ 查询用户反馈失败: {e}")
            raise

    async def get_recent_feedback(self, limit: int = 20) -> List[Telemetry]:
        """
        查询最近的反馈记录

        Args:
            limit: 返回数量限制

        Returns:
            遥测记录列表
        """
        try:
            return (
                self.db.query(Telemetry)
                .order_by(Telemetry.created_at.desc())
                .limit(limit)
                .all()
            )
        except Exception as e:
            print(f"❌ 查询最近反馈失败: {e}")
            raise

    async def get_average_rating(self, days: Optional[int] = None) -> float:
        """
        计算平均评分

        Args:
            days: 统计最近几天的数据（None 表示全部）

        Returns:
            平均评分
        """
        try:
            from sqlalchemy import func

            query = self.db.query(func.avg(Telemetry.overall_rating))

            if days is not None:
                cutoff_date = datetime.now() - timedelta(days=days)
                query = query.filter(Telemetry.created_at >= cutoff_date)

            result = query.scalar()
            return float(result) if result else 0.0

        except Exception as e:
            print(f"❌ 计算平均评分失败: {e}")
            raise

    async def get_rating_distribution(self) -> dict:
        """
        获取评分分布统计

        Returns:
            评分分布字典 {rating: count}
        """
        try:
            from sqlalchemy import func

            results = (
                self.db.query(
                    Telemetry.overall_rating, func.count(Telemetry.id).label("count")
                )
                .group_by(Telemetry.overall_rating)
                .order_by(Telemetry.overall_rating.desc())
                .all()
            )

            return {rating: count for rating, count in results}

        except Exception as e:
            print(f"❌ 获取评分分布失败: {e}")
            raise

    async def get_low_rating_feedback(
        self, threshold: int = 5, limit: int = 20
    ) -> List[Telemetry]:
        """
        查询低评分反馈（用于改进）

        Args:
            threshold: 评分阈值
            limit: 返回数量限制

        Returns:
            遥测记录列表
        """
        try:
            return (
                self.db.query(Telemetry)
                .filter(Telemetry.overall_rating <= threshold)
                .order_by(Telemetry.created_at.desc())
                .limit(limit)
                .all()
            )
        except Exception as e:
            print(f"❌ 查询低评分反馈失败: {e}")
            raise

    async def cleanup_old_data(self, days: int = 90) -> int:
        """
        清理旧数据（可选功能）

        Args:
            days: 保留最近几天的数据

        Returns:
            删除的记录数
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            deleted_count = (
                self.db.query(Telemetry)
                .filter(Telemetry.created_at < cutoff_date)
                .delete()
            )

            self.db.commit()

            print(f"✅ 已清理 {deleted_count} 条旧数据")
            return deleted_count

        except Exception as e:
            print(f"❌ 清理旧数据失败: {e}")
            self.db.rollback()
            raise
