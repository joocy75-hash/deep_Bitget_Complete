"""
테스트용 즉시 진입 전략 등록 스크립트
"""

import asyncio
import json
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

DATABASE_URL = (
    "postgresql+asyncpg://trading_user:change-this-password@localhost:5432/trading_prod"
)


async def register_strategy():
    engine = create_async_engine(DATABASE_URL, echo=True)
    AsyncSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with AsyncSessionLocal() as session:
        # 이미 존재하는지 확인
        result = await session.execute(
            text("SELECT id FROM strategies WHERE code = 'instant_entry'")
        )
        existing = result.fetchone()

        if existing:
            print(f"✅ 'instant_entry' 전략이 이미 존재합니다. ID: {existing[0]}")
            return

        # 새 전략 등록
        params = json.dumps(
            {
                "symbol": "BTCUSDT",
                "timeframe": "1m",
                "leverage": 1,
                "position_size_percent": 5,
                "stop_loss_percent": 2.0,
                "take_profit_percent": 3.0,
            }
        )

        insert_query = text("""
            INSERT INTO strategies (name, description, code, params, type, symbol, timeframe, is_active, user_id)
            VALUES (
                '🧪 테스트 즉시 진입 전략',
                '봇 시작 즉시 진입하는 테스트용 전략입니다. 실거래에는 사용하지 마세요.',
                'instant_entry',
                :params,
                'instant_entry',
                'BTCUSDT',
                '1m',
                true,
                1
            )
            RETURNING id
        """)

        result = await session.execute(insert_query, {"params": params})
        strategy_id = result.fetchone()[0]
        await session.commit()

        print(f"✅ 테스트 전략 등록 완료! ID: {strategy_id}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(register_strategy())
