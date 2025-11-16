"""
Pydantic 数据模型定义

定义 API 请求和响应的数据结构。
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


# ==================== 消息相关模型 ====================

class Message(BaseModel):
    """单条消息模型"""
    role: str = Field(..., description="消息角色: system, user, assistant")
    content: str = Field(..., description="消息内容")
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        """验证角色类型"""
        allowed_roles = ['system', 'user', 'assistant']
        if v not in allowed_roles:
            raise ValueError(f"角色必须是以下之一: {', '.join(allowed_roles)}")
        return v


# ==================== Chat API 相关模型 ====================

class ChatRequest(BaseModel):
    """Chat API 请求模型"""
    character: str = Field(..., description="角色名称，如 tocqueville")
    messages: List[Message] = Field(..., description="对话历史记录")
    stream: bool = Field(default=False, description="是否使用流式输出")
    temperature: float = Field(default=0.5, ge=0.0, le=2.0, description="模型采样温度")
    
    @field_validator('character')
    @classmethod
    def validate_character(cls, v: str) -> str:
        """验证角色名称"""
        # 这里可以添加更严格的验证
        return v.lower().strip()
    
    @field_validator('messages')
    @classmethod
    def validate_messages(cls, v: List[Message]) -> List[Message]:
        """验证消息列表"""
        if not v:
            raise ValueError("消息列表不能为空")
        return v


class ChatResponseMessage(BaseModel):
    """Chat 响应消息"""
    role: str = Field(default="assistant", description="消息角色")
    content: str = Field(..., description="消息内容")


class ChatResponseResult(BaseModel):
    """Chat 响应结果"""
    message: ChatResponseMessage = Field(..., description="响应消息")
    finish_reason: str = Field(default="stop", description="完成原因")


class TokenUsage(BaseModel):
    """Token 使用统计"""
    prompt_tokens: int = Field(default=0, description="输入 token 数量")
    completion_tokens: int = Field(default=0, description="输出 token 数量")
    total_tokens: int = Field(default=0, description="总 token 数量")
    prompt_tokens_details: Optional[Dict[str, int]] = Field(
        default=None,
        description="输入 token 详情"
    )


class ChatResponse(BaseModel):
    """Chat API 响应模型（非流式）"""
    result: ChatResponseResult = Field(..., description="响应结果")
    usage: TokenUsage = Field(..., description="Token 使用统计")
    created: int = Field(..., description="创建时间戳（秒）")
    id: str = Field(..., description="响应 ID")


# ==================== 流式响应相关模型 ====================

class StreamDelta(BaseModel):
    """流式响应增量"""
    role: Optional[str] = Field(default=None, description="消息角色")
    content: str = Field(default="", description="增量内容")


class StreamResult(BaseModel):
    """流式响应结果"""
    delta: StreamDelta = Field(..., description="增量数据")
    finish_reason: Optional[str] = Field(default=None, description="完成原因")


class StreamResponse(BaseModel):
    """流式响应模型"""
    result: Optional[StreamResult] = Field(default=None, description="响应结果")
    usage: Optional[TokenUsage] = Field(default=None, description="Token 使用统计")
    created: int = Field(..., description="创建时间戳（秒）")
    id: str = Field(..., description="响应 ID")


# ==================== Telemetry API 相关模型 ====================

class Rating(BaseModel):
    """用户评分模型"""
    overall_rating: int = Field(..., ge=1, le=10, description="整体评分（1-10）")
    comment: Optional[str] = Field(default=None, description="用户评论")


class TelemetryRequest(BaseModel):
    """Telemetry API 请求模型"""
    user_id: str = Field(..., description="用户 UUID")
    rating: Rating = Field(..., description="用户评分")
    messages: List[Message] = Field(..., description="对话消息记录")
    
    @field_validator('messages')
    @classmethod
    def validate_messages(cls, v: List[Message]) -> List[Message]:
        """验证消息列表"""
        if not v:
            raise ValueError("消息列表不能为空")
        return v


class TelemetryResponse(BaseModel):
    """Telemetry API 响应模型"""
    result: str = Field(default="ok", description="处理结果")


# ==================== 错误响应模型 ====================

class ErrorDetail(BaseModel):
    """错误详情"""
    code: str = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    details: Optional[str] = Field(default=None, description="详细信息")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: ErrorDetail = Field(..., description="错误详情")


# ==================== 健康检查模型 ====================

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(default="healthy", description="服务状态")
    timestamp: datetime = Field(default_factory=datetime.now, description="检查时间")
    version: str = Field(..., description="API 版本")