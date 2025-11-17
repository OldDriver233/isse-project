"""
Telemetry API 路由

处理用户反馈遥测数据的收集。
"""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.schemas import TelemetryRequest, TelemetryResponse, ErrorResponse
from app.services.telemetry_service import TelemetryService
from app.database import get_db

router = APIRouter()


@router.post(
    "/telemetry",
    response_model=TelemetryResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"},
    },
    summary="提交用户反馈",
    description="收集用户对 AI 对话的评价和反馈数据",
)
async def telemetry_endpoint(request: TelemetryRequest, db: Session = Depends(get_db)):
    """
    Telemetry API 端点

    **请求体示例：**
    ```json
    {
        "user_id": "8f9678c0-979f-40b9-b0e8-d4544ae77b66",
        "rating": {
            "overall_rating": 8,
            "comment": "回答很有深度，但有些地方过于学术化"
        },
        "messages": [
            {
                "role": "assistant",
                "content": "我曾亲身踏足美洲大陆..."
            }
        ]
    }
    ```

    **响应体示例：**
    ```json
    {
        "result": "ok"
    }
    ```
    """
    try:
        # 创建遥测服务实例
        telemetry_service = TelemetryService(db)

        # 保存用户反馈
        success = await telemetry_service.save_feedback(
            user_id=request.user_id, rating=request.rating, messages=request.messages
        )

        if success:
            return TelemetryResponse(result="ok")
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": {"code": "SAVE_FAILED", "message": "保存反馈数据失败"}
                },
            )

    except ValueError as e:
        # 参数验证错误
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "INVALID_REQUEST", "message": str(e)}},
        )

    except Exception as e:
        # 其他错误
        print(f"❌ Telemetry API 错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "服务器内部错误",
                    "details": str(e),
                }
            },
        )


@router.get(
    "/telemetry/stats",
    summary="获取反馈统计",
    description="获取用户反馈的统计信息（可选功能）",
)
async def get_telemetry_stats(db: Session = Depends(get_db)):
    """
    获取反馈统计信息

    **响应体示例：**
    ```json
    {
        "average_rating": 7.5,
        "total_feedback": 150,
        "rating_distribution": {
            "10": 20,
            "9": 35,
            "8": 40,
            "7": 25,
            "6": 15,
            "5": 10,
            "4": 3,
            "3": 1,
            "2": 0,
            "1": 1
        }
    }
    ```
    """
    try:
        telemetry_service = TelemetryService(db)

        # 获取统计数据
        avg_rating = await telemetry_service.get_average_rating()
        rating_dist = await telemetry_service.get_rating_distribution()

        # 计算总反馈数
        total_feedback = sum(rating_dist.values())

        return {
            "average_rating": round(avg_rating, 2),
            "total_feedback": total_feedback,
            "rating_distribution": rating_dist,
        }

    except Exception as e:
        print(f"❌ 获取统计信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "STATS_ERROR",
                    "message": "获取统计信息失败",
                    "details": str(e),
                }
            },
        )
