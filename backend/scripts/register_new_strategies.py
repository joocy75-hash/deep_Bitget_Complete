"""
새로운 검증된 전략 등록 스크립트
- RSI 평균회귀 전략
- 볼린저 밴드 스캘핑 전략
"""

import asyncio
import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from src.database.models import Strategy

async def register_new_strategies():
    """새로운 전략 등록"""

    # DB 연결
    database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./trading.db")
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    strategies_to_register = [
        {
            "code": "proven_rsi_meanreversion",
            "name": "📈 RSI 평균회귀 전략",
            "description": "과매수/과매도 구간에서 반등 포착 - 횡보장 최적화 (승률 55-60%)",
            "params": json.dumps({
                "symbol": "BTC/USDT",
                "timeframe": "15m",
                "leverage": 7,
                "position_size_percent": 30,
                "rsi_period": 14,
                "rsi_oversold": 30,
                "rsi_overbought": 70,
                "volume_multiplier": 1.2,
                "stop_loss_percent": 1.5,
                "take_profit_percent": 2.5
            }),
            "is_active": True,
            "user_id": None  # 공용 전략
        },
        {
            "code": "proven_bollinger_scalping",
            "name": "⚡ 볼린저 밴드 스캘핑 전략",
            "description": "밴드 터치 시 반등 포착 - 작은 수익 반복 (승률 60-65%)",
            "params": json.dumps({
                "symbol": "BTC/USDT",
                "timeframe": "5m",
                "leverage": 5,
                "position_size_percent": 20,
                "bb_period": 20,
                "bb_std": 2.0,
                "rsi_period": 14,
                "rsi_buy_level": 40,
                "rsi_sell_level": 60,
                "volume_multiplier": 1.1,
                "stop_loss_percent": 1.0,
                "take_profit_percent": 1.5
            }),
            "is_active": True,
            "user_id": None  # 공용 전략
        }
    ]

    async with async_session() as session:
        async with session.begin():
            for strategy_data in strategies_to_register:
                # 이미 존재하는지 확인
                result = await session.execute(
                    select(Strategy).where(Strategy.code == strategy_data["code"])
                )
                existing = result.scalar_one_or_none()

                if existing:
                    print(f"⚠️  Strategy '{strategy_data['name']}' already exists (ID: {existing.id})")
                    # 파라미터 업데이트
                    existing.params = strategy_data["params"]
                    existing.description = strategy_data["description"]
                    print(f"   ✅ Updated parameters and description")
                else:
                    # 새로 생성
                    new_strategy = Strategy(
                        code=strategy_data["code"],
                        name=strategy_data["name"],
                        description=strategy_data["description"],
                        params=strategy_data["params"],
                        is_active=strategy_data["is_active"],
                        user_id=strategy_data["user_id"]
                    )
                    session.add(new_strategy)
                    print(f"✅ Registered new strategy: {strategy_data['name']}")

            await session.commit()
            print("\n🎉 All new strategies registered successfully!")

            # 등록된 모든 전략 확인
            result = await session.execute(
                select(Strategy).where(Strategy.user_id.is_(None)).order_by(Strategy.id)
            )
            all_strategies = result.scalars().all()

            print("\n📊 Available Public Strategies:")
            print("=" * 80)
            for s in all_strategies:
                print(f"ID {s.id}: {s.name}")
                print(f"   Code: {s.code}")
                print(f"   Description: {s.description}")
                params = json.loads(s.params)
                print(f"   Timeframe: {params.get('timeframe', 'N/A')}, Leverage: {params.get('leverage', 'N/A')}x")
                print()

if __name__ == "__main__":
    asyncio.run(register_new_strategies())
