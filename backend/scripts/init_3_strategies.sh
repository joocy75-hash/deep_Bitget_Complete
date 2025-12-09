#!/bin/bash
# 전략 초기화 스크립트
# 서버에서 실행: bash scripts/init_3_strategies.sh

echo "=== 전략 초기화 시작 ==="

# 모든 전략 삭제 후 3가지 대표 전략 등록
docker exec -i db psql -U postgres -d trading << 'EOF'
-- 모든 기존 전략 삭제
DELETE FROM strategies;

-- 3가지 대표 전략 등록
INSERT INTO strategies (name, description, code, params, is_active, user_id)
VALUES 
(
    '보수적 EMA 크로스오버 전략',
    '안정적인 수익을 추구하는 전략입니다. EMA 골든크로스와 거래량 확인을 통해 명확한 추세에서만 진입합니다. 초보자에게 추천합니다.',
    'proven_conservative',
    '{"symbol": "BTCUSDT", "timeframe": "4h", "type": "proven_conservative", "ema_short": 20, "ema_long": 50, "leverage": 5, "stop_loss_percent": 4.0, "take_profit_percent": 8.0, "position_size_percent": 20}',
    true,
    NULL
),
(
    '균형적 RSI 다이버전스 전략',
    '중간 수준의 위험과 수익을 추구합니다. RSI 다이버전스와 MACD 크로스오버를 함께 확인하여 반전 지점을 포착합니다.',
    'proven_balanced',
    '{"symbol": "BTCUSDT", "timeframe": "1h", "type": "proven_balanced", "rsi_period": 14, "macd_fast": 12, "macd_slow": 26, "leverage": 8, "stop_loss_percent": 2.0, "take_profit_percent": 4.0, "position_size_percent": 30}',
    true,
    NULL
),
(
    '공격적 모멘텀 브레이크아웃 전략',
    '높은 수익 잠재력을 가진 전략입니다. 볼린저 밴드 돌파와 강한 추세(ADX) 및 거래량 급증을 확인하고 진입합니다. 경험자에게 추천합니다.',
    'proven_aggressive',
    '{"symbol": "BTCUSDT", "timeframe": "1h", "type": "proven_aggressive", "bb_period": 20, "adx_threshold": 25, "leverage": 10, "stop_loss_percent": 1.5, "take_profit_percent": 4.0, "position_size_percent": 40}',
    true,
    NULL
);

-- 결과 확인
SELECT id, name, code FROM strategies ORDER BY id;
EOF

echo "=== 전략 초기화 완료 ==="
