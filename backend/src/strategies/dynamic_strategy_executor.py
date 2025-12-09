"""
동적 전략 실행기
사용자가 생성한 전략 코드를 안전하게 실행
"""

import logging
from typing import Dict, List, Optional
import numpy as np

logger = logging.getLogger(__name__)


class DynamicStrategyExecutor:
    """동적으로 전략 코드를 실행하는 클래스"""

    def __init__(self, strategy_code: str, params: Dict):
        """
        Args:
            strategy_code: Python 전략 코드 문자열
            params: 전략 파라미터
        """
        self.strategy_code = strategy_code
        self.params = params
        self.namespace = {}

        # 안전한 실행 환경 설정
        self._setup_safe_environment()

        # 전략 코드 컴파일
        self._compile_strategy()

    def _setup_safe_environment(self):
        """안전한 실행 환경 설정"""
        # 기본 함수들 제공
        self.namespace.update(
            {
                "np": np,
                "abs": abs,
                "min": min,
                "max": max,
                "sum": sum,
                "len": len,
                "range": range,
                "enumerate": enumerate,
                "zip": zip,
                "print": logger.info,  # print를 로깅으로 리다이렉트
            }
        )

        # 기술적 지표 계산 함수들
        self.namespace.update(
            {
                "calculate_rsi": self._calculate_rsi,
                "calculate_ema": self._calculate_ema,
                "calculate_sma": self._calculate_sma,
                "calculate_macd": self._calculate_macd,
                "calculate_bollinger_bands": self._calculate_bollinger_bands,
                "calculate_atr": self._calculate_atr,
                "calculate_adx": self._calculate_adx,
            }
        )

    def _compile_strategy(self):
        """전략 코드 컴파일"""
        try:
            exec(self.strategy_code, self.namespace)
            logger.info("Strategy code compiled successfully")
        except Exception as e:
            logger.error(f"Failed to compile strategy code: {e}", exc_info=True)
            raise

    def generate_signal(
        self,
        current_price: float,
        candles: List[Dict],
        current_position: Optional[Dict] = None,
    ) -> Dict:
        """
        전략 시그널 생성

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
        try:
            # 전략 함수 확인
            if "check_entry_signal" not in self.namespace:
                logger.warning("check_entry_signal function not found in strategy code")
                return self._default_hold_signal()

            # 진입 시그널 확인
            signal = self.namespace["check_entry_signal"](candles, self.params)

            # 포지션이 없으면 진입 시그널 확인 (None 또는 빈 딕셔너리)
            if not current_position:  # None, {}, [] 모두 False
                if signal == "LONG":
                    logger.info(f"🟢 LONG signal detected, creating buy signal")
                    return self._create_buy_signal(current_price, candles)
                elif signal == "SHORT":
                    logger.info(f"🔴 SHORT signal detected, creating sell signal")
                    return self._create_sell_signal(current_price, candles)
                else:
                    return self._default_hold_signal()

            # 포지션이 있으면 청산 조건 확인
            else:
                if self._should_exit_position(current_position, current_price, candles):
                    return {
                        "action": "close",
                        "confidence": 0.8,
                        "reason": "Exit condition met",
                        "stop_loss": None,
                        "take_profit": None,
                        "size": current_position.get("quantity", 0),
                    }
                else:
                    return self._default_hold_signal()

        except Exception as e:
            logger.error(f"Error generating signal: {e}", exc_info=True)
            return self._default_hold_signal()

    def _create_buy_signal(self, current_price: float, candles: List[Dict]) -> Dict:
        """매수 시그널 생성"""
        # 손절/익절 계산
        stop_loss = None
        take_profit = None

        if "calculate_stop_loss" in self.namespace:
            try:
                stop_loss = self.namespace["calculate_stop_loss"](
                    current_price, "LONG", self.params
                )
            except Exception as e:
                logger.warning(f"Failed to calculate stop loss: {e}")

        if "calculate_take_profit" in self.namespace:
            try:
                take_profit = self.namespace["calculate_take_profit"](
                    current_price, "LONG", self.params
                )
            except Exception as e:
                logger.warning(f"Failed to calculate take profit: {e}")

        # 포지션 크기 계산
        # 주의: 실제 잔고는 bot_runner에서 전달받아야 하지만,
        # 현재는 전략 레벨에서 계산할 수 없으므로 size를 None으로 반환하고
        # bot_runner에서 실제 잔고 기반으로 계산하도록 함
        size = None  # bot_runner에서 계산
        if "calculate_position_size" in self.namespace:
            # 전략에서 position_size_percent 정보만 반환
            try:
                # 비율만 저장 (실제 계산은 bot_runner에서)
                position_size_percent = (
                    self.params.get("position_size_percent", 40) / 100
                )
                leverage = self.params.get("leverage", 10)
                # 참고용 메타데이터만 포함
                size_metadata = {
                    "position_size_percent": position_size_percent,
                    "leverage": leverage,
                }
            except Exception as e:
                logger.warning(f"Failed to get position size params: {e}")
                size_metadata = None
        else:
            size_metadata = None

        return {
            "action": "buy",
            "confidence": 0.75,
            "reason": "Entry signal detected (LONG)",
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "size": size,  # None으로 반환하여 bot_runner에서 계산하도록 함
            "size_metadata": size_metadata,  # 비율 정보 전달
        }

    def _create_sell_signal(self, current_price: float, candles: List[Dict]) -> Dict:
        """매도 시그널 생성"""
        # 손절/익절 계산
        stop_loss = None
        take_profit = None

        if "calculate_stop_loss" in self.namespace:
            try:
                stop_loss = self.namespace["calculate_stop_loss"](
                    current_price, "SHORT", self.params
                )
            except Exception as e:
                logger.warning(f"Failed to calculate stop loss: {e}")

        if "calculate_take_profit" in self.namespace:
            try:
                take_profit = self.namespace["calculate_take_profit"](
                    current_price, "SHORT", self.params
                )
            except Exception as e:
                logger.warning(f"Failed to calculate take profit: {e}")

        # 포지션 크기 계산
        # bot_runner에서 실제 잔고 기반으로 계산하도록 None 반환
        size = None  # bot_runner에서 계산
        if "calculate_position_size" in self.namespace:
            try:
                position_size_percent = (
                    self.params.get("position_size_percent", 40) / 100
                )
                leverage = self.params.get("leverage", 10)
                size_metadata = {
                    "position_size_percent": position_size_percent,
                    "leverage": leverage,
                }
            except Exception as e:
                logger.warning(f"Failed to get position size params: {e}")
                size_metadata = None
        else:
            size_metadata = None

        return {
            "action": "sell",
            "confidence": 0.75,
            "reason": "Entry signal detected (SHORT)",
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "size": size,  # None으로 반환
            "size_metadata": size_metadata,  # 비율 정보 전달
        }

    def _should_exit_position(
        self, position: Dict, current_price: float, candles: List[Dict]
    ) -> bool:
        """포지션 청산 여부 확인"""
        try:
            # 손절/익절 체크
            entry_price = position.get("entry_price", 0)
            side = position.get("side", "LONG")

            if side == "LONG":
                # 손절
                if "stop_loss" in position and position["stop_loss"]:
                    if current_price <= position["stop_loss"]:
                        return True
                # 익절
                if "take_profit" in position and position["take_profit"]:
                    if current_price >= position["take_profit"]:
                        return True
            else:  # SHORT
                # 손절
                if "stop_loss" in position and position["stop_loss"]:
                    if current_price >= position["stop_loss"]:
                        return True
                # 익절
                if "take_profit" in position and position["take_profit"]:
                    if current_price <= position["take_profit"]:
                        return True

            # 부분 익절 체크 (함수가 정의되어 있으면)
            if "should_partial_exit" in self.namespace:
                should_exit, _ = self.namespace["should_partial_exit"](
                    position, current_price, candles, self.params
                )
                if should_exit:
                    return True

            return False

        except Exception as e:
            logger.error(f"Error checking exit condition: {e}", exc_info=True)
            return False

    def _default_hold_signal(self) -> Dict:
        """기본 홀드 시그널"""
        return {
            "action": "hold",
            "confidence": 0.5,
            "reason": "No signal",
            "stop_loss": None,
            "take_profit": None,
            "size": 0,
        }

    # ===== 기술적 지표 계산 함수들 =====

    def _calculate_rsi(self, candles: List[Dict], period: int = 14) -> List[float]:
        """RSI 계산"""
        closes = [c["close"] for c in candles]
        if len(closes) < period + 1:
            return [50.0] * len(closes)

        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])

        rsi_values = [50.0] * period

        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period

            if avg_loss == 0:
                rsi_values.append(100.0)
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                rsi_values.append(rsi)

        return rsi_values

    def _calculate_ema(self, candles: List[Dict], period: int) -> List[float]:
        """EMA 계산"""
        closes = [c["close"] for c in candles]
        if len(closes) < period:
            return [closes[0]] * len(closes)

        ema_values = [np.mean(closes[:period])]
        multiplier = 2 / (period + 1)

        for i in range(period, len(closes)):
            ema = (closes[i] - ema_values[-1]) * multiplier + ema_values[-1]
            ema_values.append(ema)

        # 앞부분 패딩
        return [ema_values[0]] * (period - 1) + ema_values

    def _calculate_sma(self, candles: List[Dict], period: int) -> List[float]:
        """SMA 계산"""
        closes = [c["close"] for c in candles]
        if len(closes) < period:
            return [closes[0]] * len(closes)

        sma_values = []
        for i in range(len(closes)):
            if i < period - 1:
                sma_values.append(np.mean(closes[: i + 1]))
            else:
                sma_values.append(np.mean(closes[i - period + 1 : i + 1]))

        return sma_values

    def _calculate_macd(
        self, candles: List[Dict], fast: int = 12, slow: int = 26, signal: int = 9
    ) -> tuple:
        """MACD 계산"""
        ema_fast = self._calculate_ema(candles, fast)
        ema_slow = self._calculate_ema(candles, slow)

        macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]

        # Signal line (MACD의 EMA)
        macd_candles = [{"close": m} for m in macd_line]
        signal_line = self._calculate_ema(macd_candles, signal)

        histogram = [m - s for m, s in zip(macd_line, signal_line)]

        return macd_line, signal_line, histogram

    def _calculate_bollinger_bands(
        self, candles: List[Dict], period: int = 20, std_dev: float = 2.0
    ) -> tuple:
        """볼린저 밴드 계산"""
        closes = [c["close"] for c in candles]
        if len(closes) < period:
            avg = np.mean(closes)
            return [avg] * len(closes), [avg] * len(closes), [avg] * len(closes)

        middle_band = self._calculate_sma(candles, period)
        upper_band = []
        lower_band = []

        for i in range(len(closes)):
            if i < period - 1:
                std = np.std(closes[: i + 1])
            else:
                std = np.std(closes[i - period + 1 : i + 1])

            upper_band.append(middle_band[i] + std_dev * std)
            lower_band.append(middle_band[i] - std_dev * std)

        return upper_band, middle_band, lower_band

    def _calculate_atr(self, candles: List[Dict], period: int = 14) -> List[float]:
        """ATR 계산"""
        if len(candles) < 2:
            return [0.0] * len(candles)

        true_ranges = []
        for i in range(1, len(candles)):
            high = candles[i]["high"]
            low = candles[i]["low"]
            prev_close = candles[i - 1]["close"]

            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            true_ranges.append(tr)

        atr_values = [true_ranges[0]] if true_ranges else [0.0]

        for i in range(1, len(true_ranges)):
            if i < period:
                atr = np.mean(true_ranges[: i + 1])
            else:
                atr = (atr_values[-1] * (period - 1) + true_ranges[i]) / period
            atr_values.append(atr)

        return [atr_values[0]] + atr_values

    def _calculate_adx(self, candles: List[Dict], period: int = 14) -> List[float]:
        """ADX 계산 (간단한 버전)"""
        if len(candles) < period + 1:
            return [25.0] * len(candles)

        # 간단한 ADX 근사값 (실제 ADX는 더 복잡함)
        atr = self._calculate_atr(candles, period)
        return [min(100, max(0, a * 2)) for a in atr]
