"""
FastAPI 应用主入口

定义应用实例、中间件和路由。
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.utils.logger import app_logger
from app.utils.middleware import RequestLoggingMiddleware, setup_exception_handlers

# 创建 FastAPI 应用实例
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="社会学大师陪伴智能体 API",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加请求日志中间件
app.add_middleware(RequestLoggingMiddleware)

# 设置全局异常处理器
setup_exception_handlers(app)


@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化操作"""
    # 初始化数据库
    init_db()
    app_logger.info("✅ 数据库初始化完成")
    app_logger.info(f"✅ {settings.PROJECT_NAME} v{settings.VERSION} 启动成功")
    app_logger.info("📚 API 文档: http://localhost:8000/docs")
    app_logger.info("🌐 服务地址: http://localhost:8000")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理操作"""
    app_logger.info(f"👋 {settings.PROJECT_NAME} 正在关闭...")


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": f"欢迎使用 {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    from datetime import datetime

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": settings.VERSION,
    }


# 注册 API 路由
from app.api import chat, telemetry

app.include_router(chat.router, prefix=settings.API_V1_PREFIX, tags=["chat"])

app.include_router(telemetry.router, prefix=settings.API_V1_PREFIX, tags=["telemetry"])
