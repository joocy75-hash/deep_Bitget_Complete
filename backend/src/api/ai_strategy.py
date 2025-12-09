"""
AI 전략 생성 API
DeepSeek AI를 사용하여 자동으로 거래 전략을 생성합니다.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
import json
import logging

from ..database.db import get_session
from ..database.models import Strategy, User
from ..utils.jwt_auth import get_current_user_id
from ..services.deepseek_service import deepseek_service
from ..middleware.rate_limit_improved import ai_strategy_limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Strategy"])


class StrategyGenerateRequest(BaseModel):
    """전략 생성 요청"""

    prompt: Optional[str] = None
    count: int = 3


class StrategyResponse(BaseModel):
    """전략 응답"""

    id: int
    name: str
    description: str
    type: str
    symbol: str
    timeframe: str
    parameters: dict


@router.post("/strategies/generate")
async def generate_strategies(
    request: StrategyGenerateRequest,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    """
    AI를 사용하여 거래 전략 생성

    - DeepSeek AI가 3개의 기본 전략을 자동 생성합니다
    - 생성된 전략은 데이터베이스에 저장됩니다

    **Rate Limit**: 시간당 5회 제한
    """
    # Rate Limit 체크 (시간당 5회)
    ai_strategy_limiter.check(user_id)

    logger.info(f"User {user_id} requested AI strategy generation")

    try:
        # DeepSeek AI로 전략 생성
        strategies_data = deepseek_service.generate_trading_strategies()

        created_strategies = []

        for strategy_data in strategies_data:
            # params JSON에 모든 파라미터 저장
            params_dict = {
                "type": strategy_data["type"],
                "symbol": strategy_data["symbol"],
                "timeframe": strategy_data["timeframe"],
                **strategy_data["parameters"],  # 추가 파라미터 병합
            }

            # 데이터베이스에 저장
            new_strategy = Strategy(
                user_id=user_id,
                name=strategy_data["name"],
                description=strategy_data.get("description", ""),
                code=strategy_data.get("code", ""),  # AI가 생성한 전략 코드
                params=json.dumps(params_dict),
                is_active=False,  # 기본적으로 비활성화
            )

            session.add(new_strategy)
            await session.flush()  # ID 생성

            created_strategies.append(
                {
                    "id": new_strategy.id,
                    "name": new_strategy.name,
                    "description": new_strategy.description,
                    "type": strategy_data["type"],
                    "symbol": strategy_data["symbol"],
                    "timeframe": strategy_data["timeframe"],
                    "parameters": strategy_data["parameters"],
                }
            )

        await session.commit()

        return {
            "success": True,
            "message": f"{len(created_strategies)}개의 전략이 생성되었습니다.",
            "strategies": created_strategies,
        }

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"전략 생성 실패: {str(e)}")


@router.get("/strategies/list")
async def list_ai_strategies(
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    """
    전략 목록 조회

    반환하는 전략:
    1. 공용 전략 (user_id=NULL, is_active=True) - 모든 사용자가 볼 수 있는 활성화된 공용 전략
    2. 현재 사용자가 생성한 전략 - 활성화 여부 무관
    """
    from sqlalchemy import select, or_

    result = await session.execute(
        select(Strategy)
        .where(
            or_(
                # 공용 전략: user_id=NULL이고 활성화된 것만
                (Strategy.user_id.is_(None)) & (Strategy.is_active == True),
                # 사용자 본인의 전략: 활성화 여부 무관
                Strategy.user_id == user_id,
            )
        )
        .order_by(Strategy.id.desc())  # 최신순 정렬
    )
    strategies = result.scalars().all()
    logger.info(
        f"[Strategy List] User {user_id}: Found {len(strategies)} strategies (including public)"
    )

    return {
        "strategies": [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description or "",
                "type": json.loads(s.params).get("type", "CUSTOM")
                if s.params
                else "CUSTOM",
                "symbol": json.loads(s.params).get("symbol", "BTC/USDT")
                if s.params
                else "BTC/USDT",
                "timeframe": json.loads(s.params).get("timeframe", "1h")
                if s.params
                else "1h",
                "parameters": json.loads(s.params) if s.params else {},
                "is_active": s.is_active if hasattr(s, "is_active") else False,
                "created_at": None,
            }
            for s in strategies
        ]
    }


@router.delete("/strategies/{strategy_id}")
async def delete_strategy(
    strategy_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    """전략 삭제"""
    from sqlalchemy import select

    result = await session.execute(
        select(Strategy).where(Strategy.id == strategy_id, Strategy.user_id == user_id)
    )
    strategy = result.scalars().first()

    if not strategy:
        raise HTTPException(status_code=404, detail="전략을 찾을 수 없습니다.")

    await session.delete(strategy)
    await session.commit()

    return {"success": True, "message": "전략이 삭제되었습니다."}


@router.get("/status")
async def get_ai_status():
    """AI 서비스 상태 확인"""
    from src.config import settings

    has_api_key = bool(settings.deepseek_api_key)

    return {
        "provider": "DeepSeek",
        "model": "deepseek-chat",
        "status": "active" if has_api_key else "inactive",
        "api_key_configured": has_api_key,
        "features": ["전략 자동 생성", "시장 분석", "AI 기반 추천"],
    }
