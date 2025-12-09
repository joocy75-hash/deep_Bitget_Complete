"""
전략 로더 - 다양한 전략을 동적으로 로드

전략 코드에 따라 적절한 전략 클래스를 반환
"""

import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def load_strategy_class(strategy_code: str, params_json: Optional[str] = None):
    """
    전략 코드에 따라 적절한 전략 인스턴스 반환

    Args:
        strategy_code: 전략 코드 (파이썬 코드 문자열 또는 전략 타입)
        params_json: 전략 파라미터 JSON 문자열

    Returns:
        전략 인스턴스 (generate_signal 메서드를 가진 객체)
    """

    params = json.loads(params_json) if params_json else {}

    try:
        # 1. 검증된 프로덕션 전략 (최우선) - 파일에서 직접 읽기
        if strategy_code == "proven_conservative":
            logger.info("Loading Proven Conservative Strategy (EMA Crossover + Volume)")
            import os

            strategy_path = os.path.join(
                os.path.dirname(__file__),
                "../strategies/proven_conservative_strategy.py",
            )
            with open(strategy_path, "r", encoding="utf-8") as f:
                strategy_code_str = f.read()
            from ..strategies.dynamic_strategy_executor import DynamicStrategyExecutor

            return DynamicStrategyExecutor(strategy_code_str, params)

        elif strategy_code == "proven_balanced":
            logger.info("Loading Proven Balanced Strategy (RSI Divergence)")
            import os

            strategy_path = os.path.join(
                os.path.dirname(__file__), "../strategies/proven_balanced_strategy.py"
            )
            with open(strategy_path, "r", encoding="utf-8") as f:
                strategy_code_str = f.read()
            from ..strategies.dynamic_strategy_executor import DynamicStrategyExecutor

            return DynamicStrategyExecutor(strategy_code_str, params)

        elif strategy_code == "proven_aggressive":
            logger.info("Loading Proven Aggressive Strategy (Momentum Breakout)")
            import os

            strategy_path = os.path.join(
                os.path.dirname(__file__), "../strategies/proven_aggressive_strategy.py"
            )
            with open(strategy_path, "r", encoding="utf-8") as f:
                strategy_code_str = f.read()
            from ..strategies.dynamic_strategy_executor import DynamicStrategyExecutor

            return DynamicStrategyExecutor(strategy_code_str, params)

        elif strategy_code == "proven_rsi_meanreversion":
            logger.info("Loading Proven RSI Mean Reversion Strategy")
            import os

            strategy_path = os.path.join(
                os.path.dirname(__file__),
                "../strategies/proven_rsi_meanreversion_strategy.py",
            )
            with open(strategy_path, "r", encoding="utf-8") as f:
                strategy_code_str = f.read()
            from ..strategies.dynamic_strategy_executor import DynamicStrategyExecutor

            return DynamicStrategyExecutor(strategy_code_str, params)

        elif strategy_code == "proven_bollinger_scalping":
            logger.info("Loading Proven Bollinger Scalping Strategy")
            import os

            strategy_path = os.path.join(
                os.path.dirname(__file__),
                "../strategies/proven_bollinger_scalping_strategy.py",
            )
            with open(strategy_path, "r", encoding="utf-8") as f:
                strategy_code_str = f.read()
            from ..strategies.dynamic_strategy_executor import DynamicStrategyExecutor

            return DynamicStrategyExecutor(strategy_code_str, params)

        elif strategy_code == "test_instant_entry" or strategy_code == "instant_entry":
            logger.info("Loading Instant Entry Strategy (Test Mode)")
            import os

            strategy_path = os.path.join(
                os.path.dirname(__file__), "../strategies/instant_entry_strategy.py"
            )
            with open(strategy_path, "r", encoding="utf-8") as f:
                strategy_code_str = f.read()
            from ..strategies.dynamic_strategy_executor import DynamicStrategyExecutor

            return DynamicStrategyExecutor(strategy_code_str, params)

        # 2. 레거시 테스트 전략들
        elif strategy_code == "safe_test_ai_strategy":
            from ..strategies.test_live_strategy import create_test_strategy

            return create_test_strategy(params)

        elif strategy_code == "aggressive_test_strategy":
            from ..strategies.aggressive_test_strategy import create_aggressive_strategy

            return create_aggressive_strategy(params)

        elif strategy_code == "ma_cross":
            from ..strategies.ma_cross_strategy import create_ma_cross_strategy

            return create_ma_cross_strategy(params)

        elif strategy_code == "ultra_aggressive":
            from ..strategies.ultra_aggressive_strategy import (
                create_ultra_aggressive_strategy,
            )

            return create_ultra_aggressive_strategy(params)

        elif strategy_code == "rsi_strategy":
            # RSI 전략 - legacy engine 사용
            logger.info("Using legacy strategy engine for RSI strategy")
            return None

        elif strategy_code == "ema":
            # EMA 전략 - legacy engine 사용
            logger.info("Using legacy strategy engine for EMA strategy")
            return None

        elif strategy_code == "breakout":
            # 돌파 전략 - legacy engine 사용
            logger.info("Using legacy strategy engine for Breakout strategy")
            return None

        # 3. 동적 전략 코드 처리 (사용자 생성 전략)
        elif (
            strategy_code and len(strategy_code.strip()) > 100
        ):  # 긴 코드는 Python 코드로 간주
            logger.info(f"Loading dynamic strategy code (length: {len(strategy_code)})")
            from ..strategies.dynamic_strategy_executor import DynamicStrategyExecutor

            return DynamicStrategyExecutor(strategy_code, params)

        else:
            # 기본 전략 (기존 strategy_engine 사용)
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

        # strategy_code가 None인 경우 빈 문자열로 변환
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

        # 레거시 응답 형식 변환
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
        # 전략 종류에 따라 다른 시그니처 사용
        if strategy_code == "ultra_aggressive":
            # Ultra Aggressive는 candles만 받음
            result = strategy.generate_signal(
                candles=candles, current_position=current_position
            )
        else:
            # 다른 전략들은 current_price도 받음
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
