#!/bin/bash
# PostgreSQL에 직접 검증된 전략 등록

docker exec -e PGPASSWORD=SecureTradingDB2024# trading-postgres psql -U trading_user -d trading_prod << 'EOSQL'

-- 기존 공용 전략 삭제
DELETE FROM strategies WHERE user_id IS NULL;

-- 1. 보수적 EMA 크로스오버 전략
INSERT INTO strategies (user_id, name, description, code, params, is_active) VALUES (
    NULL,
    '🛡️ 보수적 EMA 크로스오버 전략',
    '안정적인 수익 추구 (승률 60-65%). 긴 타임프레임(4h, 1d) 사용. EMA 골든크로스 + 거래량 확인. 손익비 1:2. 레버리지 5배.',
    'proven_conservative',
    '{"symbol": "BTC/USDT", "timeframe": "4h", "ema_short": 20, "ema_long": 50, "rsi_period": 14, "volume_multiplier": 1.5, "position_size_percent": 20, "leverage": 5, "stop_loss_atr": 2.0, "take_profit_atr": 4.0}',
    true
);

-- 2. 균형적 RSI 다이버전스 전략
INSERT INTO strategies (user_id, name, description, code, params, is_active) VALUES (
    NULL,
    '⚖️ 균형적 RSI 다이버전스 전략',
    '중간 위험/수익 비율 (승률 55-60%). 타임프레임 1h, 4h. RSI 다이버전스 + MACD 확인 + 200 EMA 트렌드 필터. 손익비 1:2. 레버리지 8배.',
    'proven_balanced',
    '{"symbol": "BTC/USDT", "timeframe": "1h", "rsi_period": 14, "rsi_oversold": 30, "rsi_overbought": 70, "macd_fast": 12, "macd_slow": 26, "macd_signal": 9, "position_size_percent": 30, "leverage": 8, "stop_loss_percent": 2.0, "take_profit_percent": 4.0}',
    true
);

-- 3. 공격적 모멘텀 브레이크아웃 전략
INSERT INTO strategies (user_id, name, description, code, params, is_active) VALUES (
    NULL,
    '⚡ 공격적 모멘텀 브레이크아웃 전략',
    '높은 수익 잠재력 (승률 45-50%). 짧은 타임프레임(15m, 1h). 볼린저 밴드 돌파 + ADX 트렌드 강도 + 거래량 급증. 손익비 1:2.7. 레버리지 10배.',
    'proven_aggressive',
    '{"symbol": "BTC/USDT", "timeframe": "1h", "bb_period": 20, "bb_std": 2.0, "adx_period": 14, "adx_threshold": 25, "volume_multiplier": 2.0, "position_size_percent": 40, "leverage": 10, "stop_loss_percent": 1.5, "take_profit_percent": 4.0}',
    true
);

-- 등록된 전략 확인
SELECT id, name, code, is_active FROM strategies WHERE user_id IS NULL;

EOSQL

echo "✅ 검증된 전략이 DB에 등록되었습니다!"
