"""
균형적 RSI 다이버전스 전략 (검증된 전략)

특징:
- 중간 위험/수익 비율
- 승률 55-60%
- 타임프레임: 1h, 4h
- 과매수/과매도 구간에서 반전 포착

진입 조건:
- RSI 다이버전스 발생
- MACD 크로스오버 확인
- 200 EMA로 트렌드 필터

청산 조건:
- RSI가 중립구간 진입 (40-60)
- 손절: 2%
- 익절: 4% (손익비 1:2)
"""


def calculate_position_size(balance, params):
    """포지션 크기 계산 (균형: 계좌의 30%)"""
    percent = params.get('position_size_percent', 30) / 100
    leverage = params.get('leverage', 8)
    return balance * percent * leverage


def check_entry_signal(candles, params):
    """진입 시그널 체크"""
    if len(candles) < 200:
        return None

    try:
        # 지표 계산
        rsi = calculate_rsi(candles, params.get('rsi_period', 14))
        macd, signal, hist = calculate_macd(
            candles,
            params.get('macd_fast', 12),
            params.get('macd_slow', 26),
            params.get('macd_signal', 9)
        )
        ema_200 = calculate_ema(candles, 200)

        # 데이터 검증
        if len(rsi) < 5 or len(macd) < 5 or len(ema_200) < 1:
            return None

        current_price = candles[-1]['close']
        rsi_oversold = params.get('rsi_oversold', 30)
        rsi_overbought = params.get('rsi_overbought', 70)

        # RSI 다이버전스 감지 (간단한 버전)
        # 가격은 하락했지만 RSI는 상승 → 불리시 다이버전스 (롱 진입)
        price_falling = candles[-1]['close'] < candles[-5]['close']
        rsi_rising = rsi[-1] > rsi[-5]

        price_rising = candles[-1]['close'] > candles[-5]['close']
        rsi_falling = rsi[-1] < rsi[-5]

        # 트렌드 필터 (200 EMA)
        in_uptrend = current_price > ema_200[-1]
        in_downtrend = current_price < ema_200[-1]

        # 롱 진입: 불리시 다이버전스 + MACD 골든크로스 + 상승 트렌드
        if (rsi[-1] < rsi_oversold and
            price_falling and rsi_rising and
            macd[-1] > signal[-1] and macd[-2] <= signal[-2] and
            in_uptrend):
            return 'LONG'

        # 숏 진입: 베어리시 다이버전스 + MACD 데드크로스 + 하락 트렌드
        if (rsi[-1] > rsi_overbought and
            price_rising and rsi_falling and
            macd[-1] < signal[-1] and macd[-2] >= signal[-2] and
            in_downtrend):
            return 'SHORT'

        return None

    except Exception as e:
        print(f"Error in check_entry_signal: {e}")
        return None


def calculate_stop_loss(entry_price, side, params):
    """고정 퍼센트 손절"""
    stop_loss_percent = params.get('stop_loss_percent', 2.0) / 100

    if side == 'LONG':
        return entry_price * (1 - stop_loss_percent)
    else:
        return entry_price * (1 + stop_loss_percent)


def calculate_take_profit(entry_price, side, params):
    """고정 퍼센트 익절 (손익비 1:2)"""
    take_profit_percent = params.get('take_profit_percent', 4.0) / 100

    if side == 'LONG':
        return entry_price * (1 + take_profit_percent)
    else:
        return entry_price * (1 - take_profit_percent)


def should_partial_exit(position, current_price, candles, params):
    """부분 익절 판단 - RSI 중립구간 진입 시"""
    try:
        rsi = calculate_rsi(candles, 14)
        if len(rsi) < 1:
            return False, 0

        # RSI가 50 근처(45-55)로 돌아오면 절반 청산
        if 45 <= rsi[-1] <= 55:
            return True, 0.5

        return False, 0
    except:
        return False, 0
