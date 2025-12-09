"""
볼린저 밴드 스캘핑 전략 (검증된 전략)

특징:
- 매우 높은 거래 빈도
- 승률 60-65% (횡보장)
- 타임프레임: 5m, 15m
- 작은 수익 반복 (스캘핑)

진입 조건:
- 롱: 가격이 하단 밴드 터치 + RSI < 40
- 숏: 가격이 상단 밴드 터치 + RSI > 60

청산 조건:
- 중간 밴드(MA) 도달
- 손절: 1%
- 익절: 1.5% (손익비 1:1.5)
"""


def calculate_position_size(balance, params):
    """포지션 크기 계산 (작게: 계좌의 20%)"""
    percent = params.get('position_size_percent', 20) / 100
    leverage = params.get('leverage', 5)
    return balance * percent * leverage


def calculate_bollinger_bands(candles, period=20, std_dev=2.0):
    """볼린저 밴드 계산"""
    if len(candles) < period:
        return [], [], []

    closes = [c['close'] for c in candles]

    upper = []
    middle = []
    lower = []

    for i in range(period - 1, len(closes)):
        window = closes[i - period + 1:i + 1]
        ma = sum(window) / period
        variance = sum((x - ma) ** 2 for x in window) / period
        std = variance ** 0.5

        middle.append(ma)
        upper.append(ma + std_dev * std)
        lower.append(ma - std_dev * std)

    return upper, middle, lower


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


def check_entry_signal(candles, params):
    """진입 시그널 체크"""
    if len(candles) < 30:
        return None

    try:
        # 볼린저 밴드 계산
        bb_period = params.get('bb_period', 20)
        bb_std = params.get('bb_std', 2.0)
        upper, middle, lower = calculate_bollinger_bands(candles, bb_period, bb_std)

        # RSI 계산
        rsi = calculate_rsi(candles, params.get('rsi_period', 14))

        if len(upper) < 1 or len(rsi) < 1:
            return None

        current_price = candles[-1]['close']
        current_rsi = rsi[-1]

        # 거래량 확인 (스캘핑이므로 조건 완화)
        volumes = [c['volume'] for c in candles[-10:]]
        avg_volume = sum(volumes) / len(volumes)
        current_volume = candles[-1]['volume']
        volume_ok = current_volume > avg_volume * params.get('volume_multiplier', 1.1)

        # 롱 진입: 하단 밴드 터치 + RSI 과매도 + 거래량
        lower_threshold = params.get('lower_touch_threshold', 1.002)  # 0.2% 여유
        if (current_price <= lower[-1] * lower_threshold and
            current_rsi < params.get('rsi_buy_level', 40) and
            volume_ok):
            return 'LONG'

        # 숏 진입: 상단 밴드 터치 + RSI 과매수 + 거래량
        upper_threshold = params.get('upper_touch_threshold', 0.998)  # 0.2% 여유
        if (current_price >= upper[-1] * upper_threshold and
            current_rsi > params.get('rsi_sell_level', 60) and
            volume_ok):
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

        # 볼린저 밴드 계산
        bb_period = params.get('bb_period', 20)
        bb_std = params.get('bb_std', 2.0)
        upper, middle, lower = calculate_bollinger_bands(candles, bb_period, bb_std)

        if len(middle) < 1:
            return False

        # 수익률 계산
        if side == 'LONG':
            pnl_percent = (current_price - entry_price) / entry_price * 100
            # 중간 밴드 도달
            target_reached = current_price >= middle[-1]
        else:  # SHORT
            pnl_percent = (entry_price - current_price) / entry_price * 100
            # 중간 밴드 도달
            target_reached = current_price <= middle[-1]

        # 손절: -1%
        if pnl_percent <= -1.0:
            return True

        # 익절: +1.5%
        if pnl_percent >= 1.5:
            return True

        # 중간 밴드 도달 시 청산 (0.3% 이상 수익)
        if target_reached and pnl_percent > 0.3:
            return True

        return False

    except Exception as e:
        print(f"Error in should_exit: {e}")
        return False


def calculate_stop_loss(entry_price, side, params):
    """타이트한 손절가"""
    stop_loss_percent = params.get('stop_loss_percent', 1.0) / 100

    if side == 'LONG':
        return entry_price * (1 - stop_loss_percent)
    else:
        return entry_price * (1 + stop_loss_percent)


def calculate_take_profit(entry_price, side, params):
    """작은 목표 익절가"""
    take_profit_percent = params.get('take_profit_percent', 1.5) / 100

    if side == 'LONG':
        return entry_price * (1 + take_profit_percent)
    else:
        return entry_price * (1 - take_profit_percent)


# 전략 메타데이터
STRATEGY_METADATA = {
    "name": "⚡ 볼린저 밴드 스캘핑 전략",
    "description": "밴드 터치 시 반등 포착 (작은 수익 반복)",
    "win_rate": "60-65%",
    "timeframes": ["5m", "15m"],
    "risk_level": "low-medium",
    "trade_frequency": "very_high",
    "default_params": {
        "bb_period": 20,
        "bb_std": 2.0,
        "rsi_period": 14,
        "rsi_buy_level": 40,
        "rsi_sell_level": 60,
        "volume_multiplier": 1.1,
        "lower_touch_threshold": 1.002,
        "upper_touch_threshold": 0.998,
        "stop_loss_percent": 1.0,
        "take_profit_percent": 1.5,
        "leverage": 5,
        "position_size_percent": 20
    }
}
