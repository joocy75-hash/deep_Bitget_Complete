# 🧪 봇 테스트 및 디버깅 가이드

## 📅 최종 업데이트: 2025-12-09

---

## 🔍 현재 진단된 상태 및 수정 사항

### ✅ 완료된 수정

1. **즉시 진입 테스트 전략 생성** (`instant_entry_strategy.py`)
   - 캔들 데이터 5개 이상 수집 후 즉시 LONG 진입
   - 최소 주문량 (0.001 BTC)
   - 손절 2%, 익절 3%

2. **전략 로더 업데이트** (`strategy_loader.py`)
   - `instant_entry` 및 `test_instant_entry` 코드 지원 추가

3. **텔레그램 알림 추가** (`bot_runner.py`)
   - 포지션 진입 시 알림 전송
   - 포지션 청산 시 알림 전송

---

## 📋 서버 진단 순서

### 1. SSH로 서버 접속

```bash
ssh user@158.247.245.197
cd /path/to/auto-dashboard
```

### 2. Docker 상태 확인

```bash
docker ps
docker-compose logs -f backend --tail 100
```

### 3. 데이터베이스 진단

```bash
# 전략 목록 확인
docker exec -it trading-postgres psql -U trading_user -d trading_prod -c "SELECT id, name, code, is_active FROM strategies;"

# 봇 상태 확인
docker exec -it trading-postgres psql -U trading_user -d trading_prod -c "SELECT * FROM bot_status;"

# API 키 확인
docker exec -it trading-postgres psql -U trading_user -d trading_prod -c "SELECT user_id, LENGTH(encrypted_api_key) as key_len FROM api_keys;"
```

### 4. 텔레그램 설정 확인

```bash
docker exec trading-backend printenv | grep TELEGRAM
```

---

## 🧪 테스트 순서

### 1. 테스트 전략 등록

서버에서 실행:

```bash
cd /path/to/auto-dashboard/backend
python register_instant_entry_strategy.py
```

또는 직접 SQL:

```sql
INSERT INTO strategies (name, description, code, params, type, symbol, timeframe, is_active, user_id)
VALUES (
    '🧪 테스트 즉시 진입 전략',
    '봇 시작 즉시 진입하는 테스트용 전략입니다. 실거래에는 사용하지 마세요.',
    'instant_entry',
    '{"symbol": "BTCUSDT", "timeframe": "1m", "leverage": 1, "position_size_percent": 5, "stop_loss_percent": 2.0, "take_profit_percent": 3.0}',
    'instant_entry',
    'BTCUSDT',
    '1m',
    true,
    1
);
```

### 2. 프론트엔드에서 테스트

1. 로그인
2. Trading 페이지로 이동
3. 전략 선택: "🧪 테스트 즉시 진입 전략"
4. 봇 시작 버튼 클릭
5. 로그에서 다음 메시지 확인:
   - `✅ Loaded strategy 'xxx'`
   - `🔄 Processing market data`
   - `🚀 Instant Entry: Triggering LONG signal!`
   - `📱 Telegram: Trade entry notification sent`

### 3. 로그 모니터링

```bash
docker-compose logs -f backend 2>&1 | grep -E "(strategy|signal|trade|position|telegram|buy|sell|LONG|SHORT)"
```

---

## 🔧 주요 체크포인트

### ✅ 잔고 업데이트 안되는 문제

**원인**: API 키 설정 또는 캐시 문제

**해결 방법**:

1. Settings에서 API 키 다시 저장
2. 브라우저 캐시 삭제
3. 백엔드 로그 확인:

   ```bash
   docker logs trading-backend 2>&1 | grep -i "balance"
   ```

### ✅ 전략 진입 안되는 문제

**가능한 원인**:

1. 전략 조건이 너무 엄격함 (볼린저밴드 + ADX + 거래량 조건 동시 충족 필요)
2. 심볼 매칭 실패 (BTC/USDT vs BTCUSDT)
3. API 키 권한 부족

**해결 방법**:

1. `instant_entry` 테스트 전략 사용
2. 로그에서 "Strategy signal" 메시지 확인
3. Bitget API 키의 거래 권한 확인

### ✅ 텔레그램 알림 안되는 문제

**확인 방법**:

```bash
docker exec trading-backend printenv | grep TELEGRAM
```

**환경 변수 설정** (`.env` 파일):

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

---

## 📱 텔레그램 봇 설정 방법

### 1. BotFather에서 봇 생성

1. Telegram에서 @BotFather 검색
2. `/newbot` 명령 실행
3. 봇 이름과 username 설정
4. 토큰 저장: `1234567890:ABCdefGHIjklMNOpqrstUVwxyz`

### 2. Chat ID 확인

1. 봇에게 아무 메시지 전송
2. 브라우저에서 접속:

   ```
   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   ```

3. `chat.id` 값 확인

### 3. 환경 변수 설정

`.env` 파일:

```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrstUVwxyz
TELEGRAM_CHAT_ID=123456789
```

### 4. 서비스 재시작

```bash
docker-compose down
docker-compose up -d
```

---

## 🚨 긴급 대응

### 봇이 의도치 않게 거래를 실행할 때

```bash
# 1. 봇 즉시 중지
docker-compose stop backend

# 2. 프론트엔드에서 수동으로 포지션 청산
# 또는 Bitget 앱/웹에서 직접 청산

# 3. 원인 분석 후 재시작
docker-compose start backend
```

### DB에서 봇 상태 강제 중지

```sql
UPDATE bot_status SET is_running = false WHERE user_id = 1;
```

---

## 📊 테스트 결과 확인

### 거래 기록 확인

```sql
SELECT * FROM trades ORDER BY created_at DESC LIMIT 10;
```

### 시그널 기록 확인

```sql
SELECT * FROM trading_signals ORDER BY timestamp DESC LIMIT 10;
```

---

## 🔄 배포 후 체크리스트

- [ ] Docker 컨테이너 정상 작동 확인
- [ ] 프론트엔드 접속 확인 (<http://158.247.245.197:3000>)
- [ ] 로그인 테스트
- [ ] 잔고 조회 확인
- [ ] 전략 목록 조회 확인
- [ ] 테스트 전략으로 봇 시작
- [ ] 로그에서 시그널 생성 확인
- [ ] 텔레그램 알림 수신 확인
- [ ] 포지션 진입 확인 (테스트 금액)
- [ ] 포지션 청산 테스트 (봇 중지)
