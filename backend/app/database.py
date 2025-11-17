"""
数据库连接和会话管理模块

使用 SQLAlchemy 管理 SQLite 数据库连接。
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import settings

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite 特定配置
    pool_pre_ping=True,  # 检查连接有效性
    echo=False,  # 生产环境设为 False
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()


def init_db():
    """
    初始化数据库，创建所有表

    在应用启动时调用此函数
    """
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    获取数据库会话的依赖注入函数

    用法:
        @app.post("/api/endpoint")
        async def endpoint(db: Session = Depends(get_db)):
            # 使用 db 进行数据库操作
            pass

    Yields:
        Session: 数据库会话对象
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
