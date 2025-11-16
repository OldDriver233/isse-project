"""
Chat API 路由

处理与 AI 智能体的对话交互。
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.schemas import ChatRequest, ChatResponse, ErrorResponse
from app.services.ai_service import ai_service

router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        404: {"model": ErrorResponse, "description": "角色不存在"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"},
        503: {"model": ErrorResponse, "description": "AI 服务不可用"}
    },
    summary="与 AI 智能体对话",
    description="发送消息给指定角色的 AI 智能体，支持流式和非流式响应"
)
async def chat_endpoint(request: ChatRequest):
    """
    Chat API 端点
    
    **请求体示例（非流式）：**
    ```json
    {
        "character": "tocqueville",
        "messages": [
            {"role": "user", "content": "托克维尔对美国民主的看法是什么？"}
        ],
        "stream": false,
        "temperature": 0.5
    }
    ```
    
    **响应体示例（非流式）：**
    ```json
    {
        "result": {
            "message": {
                "role": "assistant",
                "content": "我曾亲身踏足美洲大陆..."
            },
            "finish_reason": "stop"
        },
        "usage": {
            "prompt_tokens": 114,
            "completion_tokens": 514,
            "total_tokens": 628
        },
        "created": 1762669782,
        "id": "toc-9303a5a3-325f-4855-98b8-34de84a8a9af"
    }
    ```
    
    **流式响应：**
    当 `stream=true` 时，返回 Server-Sent Events (SSE) 格式的流式数据。
    """
    try:
        # 验证角色是否有效
        from app.config import settings
        character_lower = request.character.lower().strip()
        
        # 调用 AI 服务
        result = await ai_service.chat(
            character=request.character,
            messages=request.messages,
            temperature=request.temperature,
            stream=request.stream
        )
        
        # 如果是流式响应，返回 StreamingResponse
        if request.stream:
            return StreamingResponse(
                result,
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"  # 禁用 Nginx 缓冲
                }
            )
        
        # 非流式响应
        return result
        
    except ValueError as e:
        # 参数验证错误
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": str(e)
                }
            }
        )
    
    except KeyError as e:
        # 角色不存在
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "CHARACTER_NOT_FOUND",
                    "message": f"角色 '{request.character}' 不存在",
                    "details": f"可用角色: {', '.join(settings.AVAILABLE_NAMESPACES)}"
                }
            }
        )
    
    except ConnectionError as e:
        # AI 服务连接错误
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": {
                    "code": "AI_SERVICE_UNAVAILABLE",
                    "message": "AI 服务暂时不可用，请稍后重试",
                    "details": str(e)
                }
            }
        )
    
    except Exception as e:
        # 其他错误
        print(f"❌ Chat API 错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "服务器内部错误",
                    "details": str(e)
                }
            }
        )