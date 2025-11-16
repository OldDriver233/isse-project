"""
数据库模型测试

测试 SQLAlchemy ORM 模型的创建、验证和约束。
"""

import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Telemetry, ChatSession


class TestTelemetryModel:
    """Telemetry 模型测试"""
    
    def test_create_telemetry(self, test_db: Session):
        """测试创建遥测记录"""
        telemetry = Telemetry(
            user_id="test-user-123",
            overall_rating=8,
            comment="很好的回答",
            messages='[{"role": "user", "content": "测试"}]'
        )
        
        test_db.add(telemetry)
        test_db.commit()
        test_db.refresh(telemetry)
        
        assert telemetry.id is not None
        assert telemetry.user_id == "test-user-123"
        assert telemetry.overall_rating == 8
        assert telemetry.comment == "很好的回答"
        assert telemetry.created_at is not None
        assert isinstance(telemetry.created_at, datetime)
    
    def test_telemetry_without_comment(self, test_db: Session):
        """测试创建没有评论的遥测记录"""
        telemetry = Telemetry(
            user_id="test-user-456",
            overall_rating=7,
            comment=None,
            messages='[{"role": "user", "content": "测试"}]'
        )
        
        test_db.add(telemetry)
        test_db.commit()
        test_db.refresh(telemetry)
        
        assert telemetry.id is not None
        assert telemetry.comment is None
    
    def test_telemetry_rating_constraint_min(self, test_db: Session):
        """测试评分最小值约束"""
        telemetry = Telemetry(
            user_id="test-user-789",
            overall_rating=0,  # 小于最小值 1
            messages='[{"role": "user", "content": "测试"}]'
        )
        
        test_db.add(telemetry)
        
        with pytest.raises(IntegrityError):
            test_db.commit()
        
        test_db.rollback()
    
    def test_telemetry_rating_constraint_max(self, test_db: Session):
        """测试评分最大值约束"""
        telemetry = Telemetry(
            user_id="test-user-101",
            overall_rating=11,  # 大于最大值 10
            messages='[{"role": "user", "content": "测试"}]'
        )
        
        test_db.add(telemetry)
        
        with pytest.raises(IntegrityError):
            test_db.commit()
        
        test_db.rollback()
    
    def test_telemetry_rating_valid_range(self, test_db: Session):
        """测试评分有效范围"""
        for rating in range(1, 11):  # 1-10
            telemetry = Telemetry(
                user_id=f"test-user-{rating}",
                overall_rating=rating,
                messages='[{"role": "user", "content": "测试"}]'
            )
            
            test_db.add(telemetry)
            test_db.commit()
            test_db.refresh(telemetry)
            
            assert telemetry.overall_rating == rating
    
    def test_telemetry_missing_required_fields(self, test_db: Session):
        """测试缺少必需字段"""
        # 缺少 user_id
        with pytest.raises(Exception):
            telemetry = Telemetry(
                overall_rating=8,
                messages='[{"role": "user", "content": "测试"}]'
            )
            test_db.add(telemetry)
            test_db.commit()
        
        test_db.rollback()
        
        # 缺少 overall_rating
        with pytest.raises(Exception):
            telemetry = Telemetry(
                user_id="test-user",
                messages='[{"role": "user", "content": "测试"}]'
            )
            test_db.add(telemetry)
            test_db.commit()
        
        test_db.rollback()
    
    def test_telemetry_repr(self, test_db: Session):
        """测试字符串表示"""
        telemetry = Telemetry(
            user_id="test-user-repr",
            overall_rating=9,
            messages='[{"role": "user", "content": "测试"}]'
        )
        
        test_db.add(telemetry)
        test_db.commit()
        test_db.refresh(telemetry)
        
        repr_str = repr(telemetry)
        assert "Telemetry" in repr_str
        assert "test-user-repr" in repr_str
        assert "9" in repr_str
    
    def test_query_by_user_id(self, test_db: Session):
        """测试按用户 ID 查询"""
        # 创建多条记录
        for i in range(3):
            telemetry = Telemetry(
                user_id="test-user-query",
                overall_rating=5 + i,
                messages=f'[{{"role": "user", "content": "测试{i}"}}]'
            )
            test_db.add(telemetry)
        
        test_db.commit()
        
        # 查询
        results = test_db.query(Telemetry)\
            .filter(Telemetry.user_id == "test-user-query")\
            .all()
        
        assert len(results) == 3
        assert all(r.user_id == "test-user-query" for r in results)
    
    def test_query_by_rating(self, test_db: Session):
        """测试按评分查询"""
        # 创建不同评分的记录
        for rating in [3, 5, 8, 10]:
            telemetry = Telemetry(
                user_id=f"test-user-{rating}",
                overall_rating=rating,
                messages='[{"role": "user", "content": "测试"}]'
            )
            test_db.add(telemetry)
        
        test_db.commit()
        
        # 查询低评分
        low_ratings = test_db.query(Telemetry)\
            .filter(Telemetry.overall_rating <= 5)\
            .all()
        
        assert len(low_ratings) == 2
        assert all(r.overall_rating <= 5 for r in low_ratings)


class TestChatSessionModel:
    """ChatSession 模型测试"""
    
    def test_create_chat_session(self, test_db: Session):
        """测试创建会话记录"""
        session = ChatSession(
            id="session-123",
            user_id="user-456",
            character="tocqueville",
            message_count=5
        )
        
        test_db.add(session)
        test_db.commit()
        test_db.refresh(session)
        
        assert session.id == "session-123"
        assert session.user_id == "user-456"
        assert session.character == "tocqueville"
        assert session.message_count == 5
        assert session.created_at is not None
        assert session.updated_at is not None
    
    def test_chat_session_without_user_id(self, test_db: Session):
        """测试创建没有用户 ID 的会话（匿名会话）"""
        session = ChatSession(
            id="session-anonymous",
            user_id=None,
            character="tocqueville",
            message_count=0
        )
        
        test_db.add(session)
        test_db.commit()
        test_db.refresh(session)
        
        assert session.user_id is None
    
    def test_chat_session_default_message_count(self, test_db: Session):
        """测试默认消息数量"""
        session = ChatSession(
            id="session-default",
            character="tocqueville"
        )
        
        test_db.add(session)
        test_db.commit()
        test_db.refresh(session)
        
        assert session.message_count == 0
    
    def test_chat_session_repr(self, test_db: Session):
        """测试字符串表示"""
        session = ChatSession(
            id="session-repr",
            character="tocqueville",
            message_count=10
        )
        
        test_db.add(session)
        test_db.commit()
        test_db.refresh(session)
        
        repr_str = repr(session)
        assert "ChatSession" in repr_str
        assert "session-repr" in repr_str
        assert "tocqueville" in repr_str
        assert "10" in repr_str
    
    def test_query_by_character(self, test_db: Session):
        """测试按角色查询"""
        # 创建不同角色的会话
        for i, character in enumerate(["tocqueville", "common", "tocqueville"]):
            session = ChatSession(
                id=f"session-{i}",
                character=character,
                message_count=i
            )
            test_db.add(session)
        
        test_db.commit()
        
        # 查询特定角色
        tocqueville_sessions = test_db.query(ChatSession)\
            .filter(ChatSession.character == "tocqueville")\
            .all()
        
        assert len(tocqueville_sessions) == 2
        assert all(s.character == "tocqueville" for s in tocqueville_sessions)
    
    def test_update_message_count(self, test_db: Session):
        """测试更新消息数量"""
        session = ChatSession(
            id="session-update",
            character="tocqueville",
            message_count=0
        )
        
        test_db.add(session)
        test_db.commit()
        
        # 更新消息数量
        session.message_count = 5
        test_db.commit()
        test_db.refresh(session)
        
        assert session.message_count == 5
        assert session.updated_at > session.created_at