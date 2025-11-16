"""
中间件模块

包含请求日志、异常处理等中间件。
"""

import time
import json
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.logger import app_logger
from app.utils.exceptions import (
    AppException,
    AIServiceException,
    DatabaseException,
    ValidationException,
    CharacterNotFoundException,
    RateLimitException
)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件
    
    记录每个请求的详细信息和响应时间。
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并记录日志"""
        # 记录请求开始时间
        start_time = time.time()
        
        # 生成请求 ID
        request_id = f"{int(start_time * 1000)}"
        
        # 记录请求信息
        app_logger.info(
            f"📥 请求开始: {request.method} {request.url.path} "
            f"[ID: {request_id}] "
            f"[Client: {request.client.host if request.client else 'unknown'}]"
        )
        
        # 处理请求
        try:
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 添加自定义响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.3f}s"
            
            # 记录响应信息
            app_logger.info(
                f"📤 请求完成: {request.method} {request.url.path} "
                f"[ID: {request_id}] "
                f"[Status: {response.status_code}] "
                f"[Time: {process_time:.3f}s]"
            )
            
            return response
            
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录错误
            app_logger.error(
                f"❌ 请求失败: {request.method} {request.url.path} "
                f"[ID: {request_id}] "
                f"[Time: {process_time:.3f}s] "
                f"[Error: {str(e)}]"
            )
            
            # 重新抛出异常，让全局异常处理器处理
            raise


def setup_exception_handlers(app):
    """
    设置全局异常处理器
    
    Args:
        app: FastAPI 应用实例
    """
    
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        """处理应用自定义异常"""
        app_logger.warning(
            f"⚠️ 应用异常: {exc.code} - {exc.message} "
            f"[Path: {request.url.path}]"
        )
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details
                }
            }
        )
    
    @app.exception_handler(AIServiceException)
    async def ai_service_exception_handler(request: Request, exc: AIServiceException):
        """处理 AI 服务异常"""
        app_logger.error(
            f"🤖 AI 服务异常: {exc.code} - {exc.message} "
            f"[Path: {request.url.path}]"
        )
        
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details
                }
            }
        )
    
    @app.exception_handler(DatabaseException)
    async def database_exception_handler(request: Request, exc: DatabaseException):
        """处理数据库异常"""
        app_logger.error(
            f"💾 数据库异常: {exc.code} - {exc.message} "
            f"[Path: {request.url.path}]"
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details
                }
            }
        )
    
    @app.exception_handler(ValidationException)
    async def validation_exception_handler(request: Request, exc: ValidationException):
        """处理验证异常"""
        app_logger.warning(
            f"✋ 验证异常: {exc.code} - {exc.message} "
            f"[Path: {request.url.path}]"
        )
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details
                }
            }
        )
    
    @app.exception_handler(CharacterNotFoundException)
    async def character_not_found_handler(request: Request, exc: CharacterNotFoundException):
        """处理角色不存在异常"""
        app_logger.warning(
            f"🔍 角色不存在: {exc.code} - {exc.message} "
            f"[Path: {request.url.path}]"
        )
        
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details
                }
            }
        )
    
    @app.exception_handler(RateLimitException)
    async def rate_limit_exception_handler(request: Request, exc: RateLimitException):
        """处理速率限制异常"""
        app_logger.warning(
            f"⏱️ 速率限制: {exc.code} - {exc.message} "
            f"[Path: {request.url.path}]"
        )
        
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details
                }
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """处理未捕获的异常"""
        app_logger.error(
            f"💥 未处理异常: {type(exc).__name__} - {str(exc)} "
            f"[Path: {request.url.path}]",
            exc_info=True
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "服务器内部错误",
                    "details": str(exc) if app.debug else None
                }
            }
        )
    
    app_logger.info("✅ 全局异常处理器设置完成")