# 전략 정리 완료

## 개요

테스트 전략이 많아져서 다 정리하고 3가지 대표 전략으로 세팅했습니다.

## 3가지 대표 전략

### 1. 보수적 EMA 크로스오버 전략 (`proven_conservative`)

- **설명**: 안정적인 수익을 추구하는 전략입니다. EMA 골든크로스와 거래량 확인을 통해 명확한 추세에서만 진입합니다.
- **예상 승률**: 60-65%
- **타임프레임**: 4시간봉
- **레버리지**: 5배
- **손익비**: 1:2
- **추천 대상**: 초보자

### 2. 균형적 RSI 다이버전스 전략 (`proven_balanced`)

- **설명**: 중간 수준의 위험과 수익을 추구합니다. RSI 다이버전스와 MACD 크로스오버를 함께 확인하여 반전 지점을 포착합니다.
- **예상 승률**: 55-60%
- **타임프레임**: 1시간봉
- **레버리지**: 8배
- **손익비**: 1:2
- **추천 대상**: 중급자

### 3. 공격적 모멘텀 브레이크아웃 전략 (`proven_aggressive`)

- **설명**: 높은 수익 잠재력을 가진 전략입니다. 볼린저 밴드 돌파와 강한 추세(ADX) 및 거래량 급증을 확인하고 진입합니다.
- **예상 승률**: 45-50%
- **타임프레임**: 1시간봉
- **레버리지**: 10배
- **손익비**: 1:2.7
- **추천 대상**: 경험자

---

## 삭제된 파일들

### 전략 파일 (backend/src/strategies/)

- `aggressive_test_strategy.py` ❌
- `instant_entry_strategy.py` ❌
- `ma_cross_strategy.py` ❌
- `proven_bollinger_scalping_strategy.py` ❌
- `proven_rsi_meanreversion_strategy.py` ❌
- `test_instant_entry.py` ❌
- `test_live_strategy.py` ❌
- `ultra_aggressive_strategy.py` ❌

### 남은 파일

- `__init__.py` ✅
- `dynamic_strategy_executor.py` ✅
- `proven_aggressive_strategy.py` ✅
- `proven_balanced_strategy.py` ✅
- `proven_conservative_strategy.py` ✅

### 삭제된 스크립트

- `register_aggressive_strategy.py` ❌
- `register_instant_entry_strategy.py` ❌
- `register_test_strategy.py` ❌
- `register_default_strategies.py` ❌
- `scripts/register_new_strategies.py` ❌
- `scripts/register_proven_strategies.py` ❌
- `scripts/register_strategies_sql.sh` ❌
- `scripts/migrate_strategy_code.py` ❌

---

## 서버 배포 방법

전략을 DB에 등록하려면 서버에서 다음 스크립트를 실행하세요:

```bash
# SSH 접속
ssh root@158.247.245.197

# 백엔드 컨테이너에서 실행
cd /root/auto-dashboard
docker exec -it backend python /app/scripts/reset_strategies.py
```

---

## 프론트엔드 변경사항

`SimpleStrategyCreator.jsx` 컴포넌트가 단순화되어 3가지 대표 전략 중 하나를 클릭만 하면 바로 등록되도록 변경되었습니다.

---

## 파일 구조 (정리 후)

```
backend/
├── src/
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── dynamic_strategy_executor.py
│   │   ├── proven_conservative_strategy.py
│   │   ├── proven_balanced_strategy.py
│   │   └── proven_aggressive_strategy.py
│   └── services/
│       └── strategy_loader.py (단순화됨)
└── scripts/
    └── reset_strategies.py (새 통합 스크립트)
```
