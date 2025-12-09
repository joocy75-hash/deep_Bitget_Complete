"""
전략 로더 - 3가지 대표 전략 로드

지원하는 전략:
1. proven_conservative - 보수적 EMA 크로스오버 전략
2. proven_balanced - 균형적 RSI 다이버전스 전략
3. proven_aggressive - 공격적 모멘텀 브레이크아웃 전략
"""

import json
import logging
import os
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# 전략 파일 경로
STRATEGIES_PATH = os.path.join(os.path.dirname(__file__), "../strategies")


def load_strategy_class(strategy_code: str, params_json: Optional[str] = None):
    """
    전략 코드에 따라 적절한 전략 인스턴스 반환

    Args:
        strategy_code: 전략 코드 (proven_conservative, proven_balanced, proven_aggressive)
        params_json: 전략 파라미터 JSON 문자열

    Returns:
        전략 인스턴스 (generate_signal 메서드를 가진 객체)
    """

    params = json.loads(params_json) if params_json else {}

    try:
        # 1. 보수적 EMA 크로스오버 전략
        if strategy_code == "proven_conservative":
            logger.info("Loading Proven Conservative Strategy (EMA Crossover + Volume)")
            strategy_path = os.path.join(
                STRATEGIES_PATH, "proven_conservative_strategy.py"
            )
            with open(strategy_path, "r", encoding="utf-8") as f:
                strategy_code_str = f.read()
            from ..strategies.dynamic_strategy_executor import DynamicStrategyExecutor

            return DynamicStrategyExecutor(strategy_code_str, params)

        # 2. 균형적 RSI 다이버전스 전략
        elif strategy_code == "proven_balanced":
            logger.info("Loading Proven Balanced Strategy (RSI Divergence)")
            strategy_path = os.path.join(STRATEGIES_PATH, "proven_balanced_strategy.py")
            with open(strategy_path, "r", encoding="utf-8") as f:
                strategy_code_str = f.read()
            from ..strategies.dynamic_strategy_executor import DynamicStrategyExecutor

            return DynamicStrategyExecutor(strategy_code_str, params)

        # 3. 공격적 모멘텀 브레이크아웃 전략
        elif strategy_code == "proven_aggressive":
            logger.info("Loading Proven Aggressive Strategy (Momentum Breakout)")
            strategy_path = os.path.join(
                STRATEGIES_PATH, "proven_aggressive_strategy.py"
            )
            with open(strategy_path, "r", encoding="utf-8") as f:
                strategy_code_str = f.read()
            from ..strategies.dynamic_strategy_executor import DynamicStrategyExecutor

            return DynamicStrategyExecutor(strategy_code_str, params)

        # 4. 동적 전략 코드 처리 (사용자 커스텀 전략)
        elif strategy_code and len(strategy_code.strip()) > 100:
            logger.info(f"Loading dynamic strategy code (length: {len(strategy_code)})")
            from ..strategies.dynamic_strategy_executor import DynamicStrategyExecutor

            return DynamicStrategyExecutor(strategy_code, params)

        # 5. 기타 - 기본 전략 엔진 사용
        else:
            code_preview = strategy_code[:100] if strategy_code else "None"
            logger.info(
                f"Using legacy strategy engine, code length: {len(strategy_code) if strategy_code else 0}, preview: {code_preview}"
            )
            return None

    except Exception as e:
        logger.error(f"Failed to load strategy: {e}", exc_info=True)
        return None


def generate_signal_with_strategy(
    strategy_code: Optional[str],
    current_price: float,
    candles: list,
    params_json: Optional[str] = None,
    current_position: Optional[Dict] = None,
) -> Dict:
    """
    전략을 사용하여 시그널 생성

    Returns:
        {
            "action": "buy" | "sell" | "hold" | "close",
            "confidence": 0.0 ~ 1.0,
            "reason": str,
            "stop_loss": float,
            "take_profit": float,
            "size": float
        }
    """

    strategy = load_strategy_class(strategy_code, params_json)

    if strategy is None:
        # 기본 전략 사용 (기존 strategy_engine)
        from ..services.strategy_engine import run as run_legacy_strategy

        safe_strategy_code = strategy_code or ""

        signal = run_legacy_strategy(
            strategy_code=safe_strategy_code,
            price=current_price,
            candles=candles,
            params_json=params_json,
            symbol="",
        )

        logger.info(
            f"Legacy strategy signal: {signal} (code: {safe_strategy_code[:50] if safe_strategy_code else 'None'})"
        )

        return {
            "action": signal,
            "confidence": 0.5,
            "reason": "Legacy strategy engine",
            "stop_loss": None,
            "take_profit": None,
            "size": 0.001,
        }

    # 새로운 전략 클래스 사용
    try:
        result = strategy.generate_signal(
            current_price=current_price,
            candles=candles,
            current_position=current_position,
        )
        return result

    except Exception as e:
        logger.error(f"Strategy signal generation error: {e}", exc_info=True)
        return {
            "action": "hold",
            "confidence": 0.0,
            "reason": f"Error: {str(e)}",
            "stop_loss": None,
            "take_profit": None,
            "size": 0,
        }
