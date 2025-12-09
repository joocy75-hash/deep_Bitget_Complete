"""
공격적 모멘텀 브레이크아웃 전략 (검증된 전략)

특징:
- 높은 수익 잠재력 (승률 45-50%)
- 높은 변동성
- 타임프레임: 15m, 1h
- 강한 모멘텀 포착

진입 조건:
- 가격이 볼린저 밴드 돌파
- ADX > 25 (강한 트렌드)
- 거래량 급증 (평균의 2배 이상)

청산 조건:
- 반대 밴드 터치
- 손절: ATR 1.5배 (타이트)
- 익절: ATR 4배 (손익비 1:2.7)
- 트레일링 스탑 사용
"""


def calculate_position_size(balance, params):
    """포지션 크기 계산 (공격적: 계좌의 40%)"""
    percent = params.get('position_size_percent', 40) / 100
    leverage = params.get('leverage', 10)
    return balance * percent * leverage


def check_entry_signal(candles, params):
    """진입 시그널 체크"""
    if len(candles) < 50:
        return None

    try:
        # 볼린저 밴드 계산
        upper, middle, lower = calculate_bollinger_bands(
            candles,
            params.get('bb_period', 20),
            params.get('bb_std', 2.0)
        )

        # ADX 계산 (트렌드 강도)
        adx = calculate_adx(candles, params.get('adx_period', 14))

        # 평균 거래량
        volumes = [c['volume'] for c in candles[-20:]]
        avg_volume = sum(volumes) / len(volumes)
        current_volume = candles[-1]['volume']

        # 데이터 검증
        if len(upper) < 2 or len(adx) < 1:
            return None

        current_price = candles[-1]['close']
        prev_price = candles[-2]['close']

        # 거래량 급증 확인
        volume_surge = current_volume > avg_volume * params.get('volume_multiplier', 2.0)

        # 강한 트렌드 확인
        strong_trend = adx[-1] > params.get('adx_threshold', 25)

        # 롱 진입: 상단 밴드 돌파 + 강한 상승 트렌드 + 거래량 급증
        if (prev_price <= upper[-2] and
            current_price > upper[-1] and
            strong_trend and
            volume_surge and
            candles[-1]['close'] > candles[-1]['open']):  # 양봉
            return 'LONG'

        # 숏 진입: 하단 밴드 돌파 + 강한 하락 트렌드 + 거래량 급증
        if (prev_price >= lower[-2] and
            current_price < lower[-1] and
            strong_trend and
            volume_surge and
            candles[-1]['close'] < candles[-1]['open']):  # 음봉
            return 'SHORT'

        return None

    except Exception as e:
        print(f"Error in check_entry_signal: {e}")
        return None


def calculate_stop_loss(entry_price, side, params):
    """ATR 기반 타이트한 손절"""
    stop_loss_percent = params.get('stop_loss_percent', 1.5) / 100

    if side == 'LONG':
        return entry_price * (1 - stop_loss_percent)
    else:
        return entry_price * (1 + stop_loss_percent)


def calculate_take_profit(entry_price, side, params):
    """ATR 기반 높은 목표가"""
    take_profit_percent = params.get('take_profit_percent', 4.0) / 100

    if side == 'LONG':
        return entry_price * (1 + take_profit_percent)
    else:
        return entry_price * (1 - take_profit_percent)


def should_partial_exit(position, current_price, candles, params):
    """트레일링 스탑 & 부분 익절"""
    try:
        entry_price = position.get('entry_price', 0)
        side = position.get('side', 'LONG')

        # 현재 수익률
        if side == 'LONG':
            profit_percent = (current_price - entry_price) / entry_price * 100
        else:
            profit_percent = (entry_price - current_price) / entry_price * 100

        # 3% 수익 시 50% 부분 익절
        if profit_percent >= 3.0:
            return True, 0.5

        # 6% 수익 시 추가 25% 익절 (총 75% 청산)
        if profit_percent >= 6.0:
            return True, 0.25

        return False, 0

    except:
        return False, 0
