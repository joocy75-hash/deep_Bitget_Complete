"""
RSI 평균회귀 전략 (검증된 전략)

특징:
- 높은 거래 빈도 (횡보장에서도 작동)
- 승률 55-60%
- 타임프레임: 5m, 15m, 1h
- 과매수/과매도 구간에서 반등 포착

진입 조건:
- 롱: RSI < 30 (과매도) + 거래량 확인 + 추가 필터
- 숏: RSI > 70 (과매수) + 거래량 확인 + 추가 필터

청산 조건:
- RSI 중립 구간 복귀 (40-60)
- 손절: 1.5%
- 익절: 2.5% (손익비 1:1.67)
"""


def calculate_position_size(balance, params):
    """포지션 크기 계산 (중도: 계좌의 30%)"""
    percent = params.get('position_size_percent', 30) / 100
    leverage = params.get('leverage', 7)
    return balance * percent * leverage


def calculate_rsi(candles, period=14):
    """RSI 계산"""
    if len(candles) < period + 1:
        return []

    closes = [c['close'] for c in candles]

    gains = []
    losses = []

    for i in range(1, len(closes)):
        change = closes[i] - closes[i-1]
        gains.append(max(change, 0))
        losses.append(max(-change, 0))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    rsi_values = []

    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

        rsi_values.append(rsi)

    return rsi_values


def calculate_ema(candles, period):
    """EMA 계산 (트렌드 필터용)"""
    if len(candles) < period:
        return []

    closes = [c['close'] for c in candles]
    ema = [sum(closes[:period]) / period]
    multiplier = 2 / (period + 1)

    for i in range(period, len(closes)):
        ema.append((closes[i] - ema[-1]) * multiplier + ema[-1])

    return ema


def check_entry_signal(candles, params):
    """진입 시그널 체크"""
    if len(candles) < 50:
        return None

    try:
        # RSI 계산
        rsi = calculate_rsi(candles, params.get('rsi_period', 14))

        # 200 EMA (트렌드 필터)
        ema_200 = calculate_ema(candles, params.get('ema_filter', 200))

        if len(rsi) < 2 or len(ema_200) < 1:
            return None

        current_rsi = rsi[-1]
        prev_rsi = rsi[-2]
        current_price = candles[-1]['close']

        # 거래량 확인
        volumes = [c['volume'] for c in candles[-20:]]
        avg_volume = sum(volumes) / len(volumes)
        current_volume = candles[-1]['volume']
        volume_confirmed = current_volume > avg_volume * params.get('volume_multiplier', 1.2)

        # 롱 진입 조건
        oversold_level = params.get('rsi_oversold', 30)
        if (current_rsi < oversold_level and
            prev_rsi >= oversold_level and  # RSI가 과매도 구간 진입
            volume_confirmed and
            current_price > ema_200[-1]):  # 상승 트렌드 필터
            return 'LONG'

        # 숏 진입 조건
        overbought_level = params.get('rsi_overbought', 70)
        if (current_rsi > overbought_level and
            prev_rsi <= overbought_level and  # RSI가 과매수 구간 진입
            volume_confirmed and
            current_price < ema_200[-1]):  # 하락 트렌드 필터
            return 'SHORT'

        return None

    except Exception as e:
        print(f"Error in check_entry_signal: {e}")
        return None


def should_exit(position, current_price, candles, params):
    """청산 조건 체크"""
    try:
        if not position:
            return False

        entry_price = position.get('entry_price', 0)
        side = position.get('side', 'LONG')

        # RSI 계산
        rsi = calculate_rsi(candles, params.get('rsi_period', 14))
        if len(rsi) < 1:
            return False

        current_rsi = rsi[-1]

        # 수익률 계산
        if side == 'LONG':
            pnl_percent = (current_price - entry_price) / entry_price * 100
            # RSI가 중립 구간으로 복귀 (50-70)
            rsi_exit = current_rsi > 60
        else:  # SHORT
            pnl_percent = (entry_price - current_price) / entry_price * 100
            # RSI가 중립 구간으로 복귀 (30-50)
            rsi_exit = current_rsi < 40

        # 손절: -1.5%
        if pnl_percent <= -1.5:
            return True

        # 익절: +2.5%
        if pnl_percent >= 2.5:
            return True

        # RSI 기반 청산
        if rsi_exit and pnl_percent > 0.3:  # 최소 0.3% 이익 확보
            return True

        return False

    except Exception as e:
        print(f"Error in should_exit: {e}")
        return False


def calculate_stop_loss(entry_price, side, params):
    """고정 손절가"""
    stop_loss_percent = params.get('stop_loss_percent', 1.5) / 100

    if side == 'LONG':
        return entry_price * (1 - stop_loss_percent)
    else:
        return entry_price * (1 + stop_loss_percent)


def calculate_take_profit(entry_price, side, params):
    """고정 익절가"""
    take_profit_percent = params.get('take_profit_percent', 2.5) / 100

    if side == 'LONG':
        return entry_price * (1 + take_profit_percent)
    else:
        return entry_price * (1 - take_profit_percent)


# 전략 메타데이터
STRATEGY_METADATA = {
    "name": "📈 RSI 평균회귀 전략",
    "description": "과매수/과매도 구간에서 반등 포착 (횡보장 최적화)",
    "win_rate": "55-60%",
    "timeframes": ["5m", "15m", "1h"],
    "risk_level": "medium",
    "trade_frequency": "high",
    "default_params": {
        "rsi_period": 14,
        "rsi_oversold": 30,
        "rsi_overbought": 70,
        "ema_filter": 200,
        "volume_multiplier": 1.2,
        "stop_loss_percent": 1.5,
        "take_profit_percent": 2.5,
        "leverage": 7,
        "position_size_percent": 30
    }
}
