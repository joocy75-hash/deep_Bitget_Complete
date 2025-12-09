#!/usr/bin/env python3
"""
전략 초기화 스크립트

모든 기존 전략을 삭제하고 3가지 대표 전략만 등록합니다.

대표 전략 3종:
1. 보수적 EMA 크로스오버 전략 - 안정적 수익, 낮은 위험
2. 균형적 RSI 다이버전스 전략 - 중간 위험/수익
3. 공격적 모멘텀 브레이크아웃 전략 - 높은 수익 잠재력

사용법:
    python scripts/reset_strategies.py
"""

import asyncio
import sys
import os
import json

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, delete, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.database.models import Strategy


# 3가지 대표 전략 정의
REPRESENTATIVE_STRATEGIES = [
    {
        "code": "proven_conservative",
        "name": "보수적 EMA 크로스오버 전략",
        "description": "안정적인 수익을 추구하는 전략입니다. EMA 골든크로스와 거래량 확인을 통해 명확한 추세에서만 진입합니다. 초보자에게 추천합니다.",
        "params": {
            "symbol": "BTCUSDT",
            "timeframe": "4h",
            "type": "proven_conservative",
            # EMA 설정
            "ema_short": 20,
            "ema_long": 50,
            "rsi_period": 14,
            # 거래량 필터
            "volume_multiplier": 1.5,
            # 리스크 관리
            "position_size_percent": 20,
            "leverage": 5,
            "stop_loss_percent": 4.0,  # ATR 2배
            "take_profit_percent": 8.0,  # ATR 4배, 손익비 1:2
        },
    },
    {
        "code": "proven_balanced",
        "name": "균형적 RSI 다이버전스 전략",
        "description": "중간 수준의 위험과 수익을 추구합니다. RSI 다이버전스와 MACD 크로스오버를 함께 확인하여 반전 지점을 포착합니다.",
        "params": {
            "symbol": "BTCUSDT",
            "timeframe": "1h",
            "type": "proven_balanced",
            # RSI 설정
            "rsi_period": 14,
            "rsi_oversold": 30,
            "rsi_overbought": 70,
            # MACD 설정
            "macd_fast": 12,
            "macd_slow": 26,
            "macd_signal": 9,
            # 리스크 관리
            "position_size_percent": 30,
            "leverage": 8,
            "stop_loss_percent": 2.0,
            "take_profit_percent": 4.0,  # 손익비 1:2
        },
    },
    {
        "code": "proven_aggressive",
        "name": "공격적 모멘텀 브레이크아웃 전략",
        "description": "높은 수익 잠재력을 가진 전략입니다. 볼린저 밴드 돌파와 강한 추세(ADX) 및 거래량 급증을 확인하고 진입합니다. 경험자에게 추천합니다.",
        "params": {
            "symbol": "BTCUSDT",
            "timeframe": "1h",
            "type": "proven_aggressive",
            # 볼린저 밴드 설정
            "bb_period": 20,
            "bb_std": 2.0,
            # ADX 설정
            "adx_period": 14,
            "adx_threshold": 25,
            # 거래량 필터
            "volume_multiplier": 2.0,
            # 리스크 관리
            "position_size_percent": 40,
            "leverage": 10,
            "stop_loss_percent": 1.5,  # 타이트한 손절
            "take_profit_percent": 4.0,  # 손익비 1:2.7
        },
    },
]


async def reset_strategies():
    """모든 전략을 삭제하고 3가지 대표 전략만 등록"""

    # DB 연결 생성
    database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./trading.db")
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # 1. 모든 기존 전략 삭제
            print("\n🗑️  모든 기존 전략 삭제 중...")
            result = await session.execute(select(Strategy))
            existing_strategies = result.scalars().all()
            print(f"   기존 전략 수: {len(existing_strategies)}개")

            await session.execute(delete(Strategy))
            await session.commit()
            print("   ✅ 모든 전략 삭제 완료")

            # 2. 3가지 대표 전략 등록
            print("\n📝 대표 전략 3종 등록 중...")
            for strat_data in REPRESENTATIVE_STRATEGIES:
                strategy = Strategy(
                    user_id=None,  # 공용 전략 (모든 사용자가 사용 가능)
                    name=strat_data["name"],
                    description=strat_data["description"],
                    code=strat_data["code"],
                    params=json.dumps(strat_data["params"], ensure_ascii=False),
                    is_active=True,
                )
                session.add(strategy)
                print(f"   ✓ {strat_data['name']}")

            await session.commit()
            print("\n✅ 모든 전략이 성공적으로 등록되었습니다!")

            # 3. 등록된 전략 확인
            result = await session.execute(select(Strategy))
            strategies = result.scalars().all()

            print(f"\n{'=' * 60}")
            print(f"📊 등록된 전략 목록 (총 {len(strategies)}개)")
            print(f"{'=' * 60}")

            for s in strategies:
                params = json.loads(s.params) if s.params else {}
                print(f"\n[{s.id}] {s.name}")
                print(f"    코드: {s.code}")
                print(f"    설명: {s.description[:50]}...")
                print(f"    심볼: {params.get('symbol', 'N/A')}")
                print(f"    타임프레임: {params.get('timeframe', 'N/A')}")
                print(f"    레버리지: {params.get('leverage', 'N/A')}x")
                print(f"    포지션 크기: {params.get('position_size_percent', 'N/A')}%")
                print(f"    손절: {params.get('stop_loss_percent', 'N/A')}%")
                print(f"    익절: {params.get('take_profit_percent', 'N/A')}%")

        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    print("=" * 60)
    print("       전략 초기화 스크립트")
    print("       3가지 대표 전략으로 정리")
    print("=" * 60)
    asyncio.run(reset_strategies())
    print("\n" + "=" * 60)
    print("완료!")
    print("=" * 60)
