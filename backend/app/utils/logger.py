"""
日志配置模块

使用 Loguru 配置应用日志系统。
"""

import sys
from pathlib import Path
from loguru import logger

from app.config import settings


def setup_logger():
    """
    配置日志系统

    - 移除默认处理器
    - 添加控制台输出（带颜色）
    - 添加文件输出（按日期轮转）
    """
    # 移除默认处理器
    logger.remove()

    # 控制台输出配置
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> \
                | <level>{level: <8}</level> \
                | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.LOG_LEVEL,
        colorize=True,
    )

    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # 文件输出配置 - 所有日志
    logger.add(
        log_dir / "app_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="00:00",  # 每天午夜轮转
        retention="30 days",  # 保留30天
        compression="zip",  # 压缩旧日志
        encoding="utf-8",
    )

    # 文件输出配置 - 错误日志
    logger.add(
        log_dir / "error_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="00:00",
        retention="90 days",  # 错误日志保留更久
        compression="zip",
        encoding="utf-8",
    )

    logger.info(f"✅ 日志系统初始化完成 (级别: {settings.LOG_LEVEL})")

    return logger


# 创建全局 logger 实例
app_logger = setup_logger()
