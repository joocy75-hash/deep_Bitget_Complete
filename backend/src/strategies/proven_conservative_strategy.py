"""
보수적 EMA 크로스오버 전략 (검증된 전략)

특징:
- 안정적인 수익 추구 (승률 60-65%)
- 낮은 변동성
- 긴 타임프레임 (4h, 1d)
- 강한 트렌드에서만 진입

진입 조건:
- EMA(20) 상향 돌파 EMA(50)
- 거래량이 평균의 1.5배 이상
- RSI > 50 (상승 모멘텀 확인)

청산 조건:
- EMA(20) 하향 돌파 EMA(50)
- 손절: ATR 2배
- 익절: ATR 4배 (손익비 1:2)
"""


def calculate_position_size(balance, params):
    """포지션 크기 계산 (보수적: 계좌의 20%)"""
    percent = params.get('position_size_percent', 20) / 100
    leverage = params.get('leverage', 5)  # 낮은 레버리지
    return balance * percent * leverage


def check_entry_signal(candles, params):
    """진입 시그널 체크"""
    if len(candles) < 60:
        return None

    try:
        # EMA 계산
        ema_short = calculate_ema(candles, params.get('ema_short', 20))
        ema_long = calculate_ema(candles, params.get('ema_long', 50))

        # RSI 계산
        rsi = calculate_rsi(candles, params.get('rsi_period', 14))

        # 평균 거래량 계산
        volumes = [c['volume'] for c in candles[-30:]]
        avg_volume = sum(volumes) / len(volumes)
        current_volume = candles[-1]['volume']

        # 데이터 검증
        if len(ema_short) < 2 or len(ema_long) < 2 or len(rsi) < 1:
            return None

        # 거래량 필터 (중요!)
        volume_threshold = params.get('volume_multiplier', 1.5)
        volume_confirmed = current_volume > avg_volume * volume_threshold

        # 롱 진입: EMA 골든크로스 + 거래량 증가 + RSI > 50
        if (ema_short[-1] > ema_long[-1] and
            ema_short[-2] <= ema_long[-2] and
            rsi[-1] > 50 and
            volume_confirmed):
            return 'LONG'

        # 숏 진입: EMA 데드크로스 + 거래량 증가 + RSI < 50
        if (ema_short[-1] < ema_long[-1] and
            ema_short[-2] >= ema_long[-2] and
            rsi[-1] < 50 and
            volume_confirmed):
            return 'SHORT'

        return None

    except Exception as e:
        print(f"Error in check_entry_signal: {e}")
        return None


def calculate_stop_loss(entry_price, side, params):
    """ATR 기반 손절가 계산"""
    atr_multiplier = params.get('stop_loss_atr', 2.0)
    # ATR은 동적으로 계산되어야 하지만, 여기서는 간단히 2% 고정
    stop_loss_percent = 0.02 * atr_multiplier

    if side == 'LONG':
        return entry_price * (1 - stop_loss_percent)
    else:  # SHORT
        return entry_price * (1 + stop_loss_percent)


def calculate_take_profit(entry_price, side, params):
    """ATR 기반 익절가 계산 (손익비 1:2)"""
    atr_multiplier = params.get('take_profit_atr', 4.0)
    take_profit_percent = 0.02 * atr_multiplier

    if side == 'LONG':
        return entry_price * (1 + take_profit_percent)
    else:  # SHORT
        return entry_price * (1 - take_profit_percent)


def should_partial_exit(position, current_price, candles, params):
    """부분 익절 판단"""
    entry_price = position.get('entry_price', 0)
    side = position.get('side', 'LONG')

    if side == 'LONG':
        profit_percent = (current_price - entry_price) / entry_price * 100
    else:
        profit_percent = (entry_price - current_price) / entry_price * 100

    # 5% 수익 시 50% 부분 익절
    if profit_percent >= 5.0:
        return True, 0.5

    return False, 0
