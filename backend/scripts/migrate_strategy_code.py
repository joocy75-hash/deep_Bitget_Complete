"""
기존 전략의 code 필드 마이그레이션 스크립트

사용법:
    python -m scripts.migrate_strategy_code
"""

import asyncio
import json
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, update
from src.database.db import AsyncSessionLocal
from src.database.models import Strategy


async def migrate_strategy_codes():
    """code 필드가 NULL인 전략들에 대해 params의 type을 기반으로 code 설정"""

    # type → code 매핑
    type_to_code_map = {
        "golden_cross": "ma_cross",
        "rsi_reversal": "rsi_strategy",
        "trend_following": "ema",
        "breakout": "breakout",
        "aggressive": "ultra_aggressive",
        "ultra_aggressive": "ultra_aggressive",
        "ma_cross": "ma_cross",
        "rsi": "rsi_strategy",
        "ema": "ema",
    }

    async with AsyncSessionLocal() as session:
        # code가 NULL인 전략 조회
        result = await session.execute(select(Strategy).where(Strategy.code.is_(None)))
        strategies = result.scalars().all()

        print(f"Found {len(strategies)} strategies with NULL code")

        updated_count = 0
        for strategy in strategies:
            # params에서 type 추출
            try:
                params = json.loads(strategy.params) if strategy.params else {}
                strategy_type = params.get("type", "")
            except json.JSONDecodeError:
                strategy_type = ""

            # type → code 매핑
            new_code = type_to_code_map.get(strategy_type, "ema")  # 기본값: ema

            print(f"  Strategy ID {strategy.id} '{strategy.name}':")
            print(f"    - params type: '{strategy_type}'")
            print(f"    - new code: '{new_code}'")

            # code 업데이트
            strategy.code = new_code
            updated_count += 1

        if updated_count > 0:
            await session.commit()
            print(f"\n✅ Updated {updated_count} strategies")
        else:
            print("\n✅ No strategies need updating")


if __name__ == "__main__":
    print("=== Strategy Code Migration ===\n")
    asyncio.run(migrate_strategy_codes())
    print("\n=== Migration Complete ===")
