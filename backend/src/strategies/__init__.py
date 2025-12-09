"""
전략 모듈

사용 가능한 전략 (3가지 대표 전략):
1. proven_conservative - 보수적 EMA 크로스오버 전략
2. proven_balanced - 균형적 RSI 다이버전스 전략
3. proven_aggressive - 공격적 모멘텀 브레이크아웃 전략
"""

from .dynamic_strategy_executor import DynamicStrategyExecutor

__all__ = [
    "DynamicStrategyExecutor",
]

# 전략 코드 목록
STRATEGY_CODES = [
    "proven_conservative",
    "proven_balanced",
    "proven_aggressive",
]
