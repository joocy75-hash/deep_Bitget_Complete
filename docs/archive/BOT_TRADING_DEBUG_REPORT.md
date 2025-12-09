# 🔧 봇 거래 실행 안됨 문제 디버깅 & 수정 보고서

## 📅 수정일: 2025-12-09

---

## 🔍 발견된 핵심 문제점

### 1. **전략 목록 조회 문제** (`/api/strategy/list`)

- **문제**: 사용자가 생성한 전략이 목록에 표시되지 않음
- **원인**: `user_id=NULL`인 공용 전략만 반환하도록 되어 있었음
- **파일**: `backend/src/api/strategy.py`

### 2. **전략 코드(code) 필드 미설정**

- **문제**: 프론트엔드에서 전략 생성 시 `code` 필드 없이 `type`만 전송
- **원인**: 백엔드에서 `code` 없으면 `None`으로 저장 → 전략 클래스 로드 실패
- **파일**: `backend/src/api/strategy.py`

### 3. **Legacy 전략 엔진 기본값 문제**

- **문제**: `strategy_type`이 없으면 무조건 `hold` 반환
- **원인**: `strategy_engine.py`에서 type 매칭 실패 시 hold 반환
- **파일**: `backend/src/services/strategy_engine.py`

### 4. **심볼 매칭 문제**

- **문제**: CCXT는 `BTCUSDT` 형식, 전략 params는 `BTC/USDT` 형식 → 매칭 실패
- **원인**: 심볼 정규화 없이 단순 문자열 비교
- **파일**: `backend/src/services/bot_runner.py`

### 5. **텔레그램 환경변수 미설정**

- **문제**: 텔레그램 알림이 작동하지 않음
- **원인**: `docker-compose.yml`에 `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` 누락
- **파일**: `docker-compose.yml`

---

## ✅ 적용된 수정사항

### 1. 전략 목록 조회 개선 (`strategy.py`)

```python
# 수정 전: 공용 전략만 반환
select(Strategy).where(Strategy.user_id.is_(None))

# 수정 후: 공용 전략 + 사용자 본인 전략 모두 반환
select(Strategy).where(
    or_(
        (Strategy.user_id.is_(None)) & (Strategy.is_active.is_(True)),
        Strategy.user_id == user_id
    )
)
```

### 2. 전략 type → code 자동 매핑 (`strategy.py`)

```python
type_to_code_map = {
    "golden_cross": "ma_cross",
    "rsi_reversal": "rsi_strategy",
    "trend_following": "ema",
    "breakout": "breakout",
    "ultra_aggressive": "ultra_aggressive",
}
strategy_code = type_to_code_map.get(payload.type, payload.type)
```

### 3. Legacy 전략 엔진 개선 (`strategy_engine.py`)

```python
# strategy_code 기반 매핑 추가
code_to_type_map = {
    "rsi_strategy": "rsi",
    "ema": "ema",
    "ma_cross": "ema",
    "breakout": "breakout",
}

# 기본값을 EMA 전략으로 설정 (hold 대신)
if not strategy_type:
    strategy_type = "ema"
```

### 4. 심볼 정규화 (`bot_runner.py`)

```python
# 심볼 정규화: BTC/USDT, BTCUSDT, BTC-USDT 모두 BTCUSDT로 변환
normalized_market = market_symbol.replace("/", "").replace("-", "").upper()
normalized_strategy = symbol.replace("/", "").replace("-", "").upper()

if normalized_market != normalized_strategy:
    continue
```

### 5. 텔레그램 환경변수 추가 (`docker-compose.yml`)

```yaml
# Telegram Bot (optional)
TELEGRAM_BOT_TOKEN: ${TELEGRAM_BOT_TOKEN:-}
TELEGRAM_CHAT_ID: ${TELEGRAM_CHAT_ID:-}
```

---

## 🚀 배포 방법

### 1. 서버에서 코드 업데이트

```bash
cd /path/to/auto-dashboard
git pull origin main
```

### 2. Docker 컨테이너 재빌드 및 재시작

```bash
docker-compose down
docker-compose build backend
docker-compose up -d
```

### 3. 텔레그램 알림 설정 (선택사항)

`.env` 파일에 텔레그램 설정 추가:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

### 4. 로그 확인

```bash
docker-compose logs -f backend
```

---

## 📋 테스트 체크리스트

- [ ] 프론트엔드에서 전략 생성 → 목록에 표시되는지 확인
- [ ] 생성한 전략 선택 후 봇 시작
- [ ] 로그에서 "Processing market data" 메시지 확인
- [ ] 로그에서 "Strategy signal" 메시지 확인 (buy/sell 신호)
- [ ] 실제 거래 실행 여부 확인
- [ ] 텔레그램 알림 수신 여부 확인 (설정한 경우)

---

## 🔧 디버깅 팁

### 로그 레벨 변경

`main.py`에서 로그 레벨을 DEBUG로 변경하면 더 상세한 로그 확인 가능:

```python
logging.getLogger("bot_runner").setLevel(logging.DEBUG)
```

### 주요 로그 메시지

- `✅ Loaded strategy 'xxx'`: 전략 로드 성공
- `🔄 Processing market data`: 시장 데이터 처리 중
- `Strategy signal for user X: buy/sell`: 매매 신호 생성
- `📈 Order placed`: 주문 실행됨

---

## ⚠️ 주의사항

1. **기존 전략 마이그레이션**: 이미 생성된 전략 중 `code` 필드가 NULL인 경우, 수동으로 업데이트 필요

   ```sql
   UPDATE strategies SET code = 'ma_cross' WHERE code IS NULL;
   ```

2. **API 키 확인**: Bitget API 키가 유효한지, 거래 권한이 있는지 확인

3. **잔고 확인**: 최소 거래 금액(0.01 BTC) 이상의 잔고가 있는지 확인
