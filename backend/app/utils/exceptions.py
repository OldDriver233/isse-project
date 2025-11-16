"""
自定义异常类

定义应用特定的异常类型。
"""

from typing import Optional


class AppException(Exception):
    """应用基础异常类"""
    
    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        details: Optional[str] = None
    ):
        self.message = message
        self.code = code
        self.details = details
        super().__init__(self.message)


class AIServiceException(AppException):
    """AI 服务相关异常"""
    
    def __init__(
        self,
        message: str = "AI 服务错误",
        code: str = "AI_SERVICE_ERROR",
        details: Optional[str] = None
    ):
        super().__init__(message, code, details)


class DatabaseException(AppException):
    """数据库相关异常"""
    
    def __init__(
        self,
        message: str = "数据库错误",
        code: str = "DATABASE_ERROR",
        details: Optional[str] = None
    ):
        super().__init__(message, code, details)


class ValidationException(AppException):
    """数据验证异常"""
    
    def __init__(
        self,
        message: str = "数据验证失败",
        code: str = "VALIDATION_ERROR",
        details: Optional[str] = None
    ):
        super().__init__(message, code, details)


class CharacterNotFoundException(AppException):
    """角色不存在异常"""
    
    def __init__(
        self,
        character: str,
        available_characters: list
    ):
        message = f"角色 '{character}' 不存在"
        details = f"可用角色: {', '.join(available_characters)}"
        super().__init__(
            message=message,
            code="CHARACTER_NOT_FOUND",
            details=details
        )


class RateLimitException(AppException):
    """速率限制异常"""
    
    def __init__(
        self,
        message: str = "请求过于频繁",
        code: str = "RATE_LIMIT_EXCEEDED",
        details: Optional[str] = None
    ):
        super().__init__(message, code, details)