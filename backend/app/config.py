"""
配置管理模块

使用 Pydantic Settings 管理环境变量和应用配置。
"""

from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""

    # API 配置
    PROJECT_NAME: str = "Sociology Master Chat API"
    API_V1_PREFIX: str = "/api/v1"
    VERSION: str = "0.1.0"

    # 数据库配置
    DATABASE_URL: str = "sqlite:///./backend.db"

    # AI 配置 - Pinecone
    PINECONE_API_KEY: str
    PINECONE_INDEX_NAME: str = "sociology-master"

    # AI 配置 - Gemini
    GEMINI_API_KEY: str

    # CORS 配置
    ALLOWED_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        """
        解析 ALLOWED_ORIGINS 配置
        支持三种格式：
        1. JSON 数组：["http://localhost:3000", "http://localhost:5173"]
        2. 逗号分隔：http://localhost:3000,http://localhost:5173
        3. Python 列表对象
        """
        if isinstance(v, str):
            # 尝试解析 JSON 格式
            import json

            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass

            # 如果不是 JSON，按逗号分隔处理
            return [origin.strip() for origin in v.split(",") if origin.strip()]

        # 如果已经是列表，直接返回
        if isinstance(v, list):
            return v

        # 其他情况返回默认值
        return ["http://localhost:3000", "http://localhost:5173"]

    # 日志配置
    LOG_LEVEL: str = "INFO"

    # AI 模型配置
    EMBEDDING_MODEL: str = "text-embedding-004"
    CHAT_MODEL: str = "gemini-2.5-flash"
    DEFAULT_TEMPERATURE: float = 0.5
    DEFAULT_NAMESPACE: str = "common"
    AVAILABLE_NAMESPACES: List[str] = ["tocqueville", "common"]

    # RAG 配置
    RAG_TOP_K: int = 8  # 检索文档数量

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )


# 创建全局配置实例
settings = Settings()
