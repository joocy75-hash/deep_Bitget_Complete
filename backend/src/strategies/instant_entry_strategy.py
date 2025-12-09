"""
테스트용 즉시 진입 전략

봇 시작 직후 첫 번째 마켓 데이터 수신 시 즉시 진입
테스트 목적으로만 사용 - 실거래 금지!

특징:
- 캔들 데이터 5개 이상 수집 후 즉시 BUY
- 최소 주문량 (0.001 BTC)
- 손절 2%, 익절 3%
"""

# 전역 상태 (간단한 테스트용)
_entry_triggered = False


def check_entry_signal(candles, params):
    """
    즉시 진입 시그널 - 조건 충족 시 LONG 시그널 반환

    Args:
        candles: 캔들 데이터 리스트
        params: 전략 파라미터

    Returns:
        'LONG' for immediate entry, None otherwise
    """
    # 캔들이 최소 5개 이상이면 바로 진입 (테스트용: 항상 LONG)
    if len(candles) >= 5:
        print(f"🚀 Instant Entry: Triggering LONG signal! Candles: {len(candles)}")
        return "LONG"

    return None


def calculate_position_size(balance, params):
    """최소 포지션 크기 반환"""
    return 0.001  # Bitget 최소 BTC 주문량


def calculate_stop_loss(entry_price, side, params):
    """손절가 계산"""
    stop_loss_percent = params.get("stop_loss_percent", 2.0) / 100

    if side == "LONG":
        return entry_price * (1 - stop_loss_percent)
    else:
        return entry_price * (1 + stop_loss_percent)


def calculate_take_profit(entry_price, side, params):
    """익절가 계산"""
    take_profit_percent = params.get("take_profit_percent", 3.0) / 100

    if side == "LONG":
        return entry_price * (1 + take_profit_percent)
    else:
        return entry_price * (1 - take_profit_percent)


def reset_entry_state():
    """진입 상태 리셋 (테스트용)"""
    global _entry_triggered
    _entry_triggered = False
