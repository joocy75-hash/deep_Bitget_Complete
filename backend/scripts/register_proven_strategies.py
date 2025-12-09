#!/usr/bin/env python3
"""
검증된 전략 3종을 DB에 등록하는 스크립트

이 스크립트는 공용 전략(user_id=NULL)으로 등록하여
모든 사용자가 선택할 수 있도록 합니다.
"""

import asyncio
import sys
import os
import json

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.database.models import Strategy


async def register_proven_strategies():
    """검증된 전략 3종을 DB에 등록"""

    # DB 연결 생성
    database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./trading.db")
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # 전략 파일들 읽기
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    strategies_path = os.path.join(base_path, 'src', 'strategies')

    strategies_to_register = [
        {
            "code": "proven_conservative",
            "name": "🛡️ 보수적 EMA 크로스오버 전략",
            "description": "안정적인 수익 추구 (승률 60-65%). 긴 타임프레임(4h, 1d) 사용. EMA 골든크로스 + 거래량 확인. 손익비 1:2. 레버리지 5배.",
            "params": json.dumps({
                "symbol": "BTC/USDT",
                "timeframe": "4h",
                "ema_short": 20,
                "ema_long": 50,
                "rsi_period": 14,
                "volume_multiplier": 1.5,
                "position_size_percent": 20,
                "leverage": 5,
                "stop_loss_atr": 2.0,
                "take_profit_atr": 4.0
            })
        },
        {
            "code": "proven_balanced",
            "name": "⚖️ 균형적 RSI 다이버전스 전략",
            "description": "중간 위험/수익 비율 (승률 55-60%). 타임프레임 1h, 4h. RSI 다이버전스 + MACD 확인 + 200 EMA 트렌드 필터. 손익비 1:2. 레버리지 8배.",
            "params": json.dumps({
                "symbol": "BTC/USDT",
                "timeframe": "1h",
                "rsi_period": 14,
                "rsi_oversold": 30,
                "rsi_overbought": 70,
                "macd_fast": 12,
                "macd_slow": 26,
                "macd_signal": 9,
                "position_size_percent": 30,
                "leverage": 8,
                "stop_loss_percent": 2.0,
                "take_profit_percent": 4.0
            })
        },
        {
            "code": "proven_aggressive",
            "name": "⚡ 공격적 모멘텀 브레이크아웃 전략",
            "description": "높은 수익 잠재력 (승률 45-50%). 짧은 타임프레임(15m, 1h). 볼린저 밴드 돌파 + ADX 트렌드 강도 + 거래량 급증. 손익비 1:2.7. 레버리지 10배.",
            "params": json.dumps({
                "symbol": "BTC/USDT",
                "timeframe": "1h",
                "bb_period": 20,
                "bb_std": 2.0,
                "adx_period": 14,
                "adx_threshold": 25,
                "volume_multiplier": 2.0,
                "position_size_percent": 40,
                "leverage": 10,
                "stop_loss_percent": 1.5,
                "take_profit_percent": 4.0
            })
        }
    ]

    async with async_session() as session:
        try:
            # 기존 공용 전략 삭제 (user_id가 NULL인 것들)
            print("🗑️  기존 공용 전략 삭제 중...")
            await session.execute(
                delete(Strategy).where(Strategy.user_id.is_(None))
            )
            await session.commit()
            print("✅ 기존 공용 전략 삭제 완료")

            # 새로운 전략 등록
            print("\n📝 검증된 전략 등록 중...")
            for strat_data in strategies_to_register:
                strategy = Strategy(
                    user_id=None,  # 공용 전략 (모든 사용자가 사용 가능)
                    name=strat_data["name"],
                    description=strat_data["description"],
                    code=strat_data["code"],  # 짧은 식별자
                    params=strat_data["params"],
                    is_active=True  # 공용 전략은 기본 활성화
                )
                session.add(strategy)
                print(f"   ✓ {strat_data['name']}")

            await session.commit()
            print("\n✅ 모든 전략이 성공적으로 등록되었습니다!")

            # 등록된 전략 확인
            result = await session.execute(
                select(Strategy).where(Strategy.user_id.is_(None))
            )
            strategies = result.scalars().all()

            print(f"\n📊 등록된 공용 전략 목록 ({len(strategies)}개):")
            for s in strategies:
                params = json.loads(s.params) if s.params else {}
                print(f"\n{s.name}")
                print(f"  - ID: {s.id}")
                print(f"  - 코드: {s.code}")
                print(f"  - 심볼: {params.get('symbol', 'N/A')}")
                print(f"  - 타임프레임: {params.get('timeframe', 'N/A')}")
                print(f"  - 레버리지: {params.get('leverage', 'N/A')}x")
                print(f"  - 포지션 크기: {params.get('position_size_percent', 'N/A')}%")

        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    print("=" * 60)
    print("검증된 트레이딩 전략 등록 스크립트")
    print("=" * 60)
    asyncio.run(register_proven_strategies())
    print("\n" + "=" * 60)
    print("완료!")
    print("=" * 60)
