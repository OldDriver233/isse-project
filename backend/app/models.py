"""
SQLAlchemy ORM 模型定义

定义数据库表结构和关系。
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, CheckConstraint
from sqlalchemy.sql import func

from app.database import Base


class Telemetry(Base):
    """
    遥测数据表

    存储用户对 AI 对话的评价和反馈
    """

    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, nullable=False, index=True, comment="用户 UUID")
    overall_rating = Column(Integer, nullable=False, comment="整体评分（1-10）")
    comment = Column(Text, nullable=True, comment="用户评论文本")
    messages = Column(Text, nullable=False, comment="JSON 格式的消息记录")
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )

    __table_args__ = (
        CheckConstraint(
            "overall_rating >= 1 AND overall_rating <= 10", name="check_rating_range"
        ),
    )

    def __repr__(self):
        return f"<Telemetry(id={self.id}, user_id={self.user_id}, rating={self.overall_rating})>"


class ChatSession(Base):
    """
    会话表（可选）

    追踪用户的对话会话，用于分析和统计
    """

    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, comment="会话 UUID")
    user_id = Column(String, nullable=True, index=True, comment="用户 UUID（可选）")
    character = Column(String, nullable=False, index=True, comment="角色名称")
    message_count = Column(Integer, default=0, comment="消息数量")
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="最后更新时间",
    )

    def __repr__(self):
        return f"<ChatSession(id={self.id}, character={self.character}, messages={self.message_count})>"
