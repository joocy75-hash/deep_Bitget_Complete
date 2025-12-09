# 다중 전략 봇 시스템 구현 계획

## 📋 개요

현재 시스템은 사용자당 1개의 전략만 실행할 수 있습니다. 이를 개선하여 **사용자가 여러 전략을 동시에 실행하고, 각 전략에 잔고 비율을 할당**할 수 있는 시스템으로 업그레이드합니다.

### 목표
- 사용자가 여러 전략을 동시에 실행 (예: 공격적 40% + 안정적 30% + 보수적 30%)
- 각 전략마다 독립적인 잔고 비율 할당
- 전략별 성과 추적 및 비교
- 리스크 분산 투자 가능

---

## 🎯 핵심 요구사항

### 1. 기능 요구사항
- [x] 사용자당 최대 5개 전략 동시 실행
- [x] 각 전략에 잔고 비율 할당 (최소 10%, 총합 100% 이하)
- [x] 전략별 독립적인 포지션 관리
- [x] 전략별 손익 추적
- [x] 실시간 전략 추가/제거/비율 조정 (봇 중지 상태에서만)
- [x] 동일 심볼 허용 (각 전략이 독립적으로 BTC 거래 가능)

### 2. 안전 장치
- [x] 총 비율이 100%를 초과하지 않도록 검증
- [x] 최소 할당 비율 10% 강제
- [x] 잔고 부족 시 우선순위 순서로 처리 (먼저 추가된 전략 우선)
- [x] API Rate Limit 준수 (기존 최적화 유지)

### 3. 제외 사항 (1단계)
- [ ] ~~봇 실행 중 비율 실시간 조정~~ (복잡도가 높아 나중에 구현)
- [ ] ~~전략 간 심볼 중복 방지~~ (독립적 거래 허용)
- [ ] ~~전략 간 시그널 조율~~ (각 전략 독립 실행)

---

## 🏗️ 시스템 아키텍처

### 현재 구조
```
User (1) ─── BotStatus (1) ─── Strategy (1)
                └─ is_running: boolean
                └─ strategy_id: int
```

### 변경 후 구조
```
User (1) ─── BotStatus (1) ─── StrategyAllocation (N)
                └─ is_running: boolean          └─ strategy_id: int
                └─ active_strategies: JSON       └─ balance_percent: float
                                                  └─ priority: int
```

---

## 📊 데이터베이스 변경

### 1. BotStatus 테이블 수정

#### 변경 전
```python
class BotStatus(Base):
    user_id: int
    strategy_id: int  # 단일 전략
    is_running: bool
    symbol: str
```

#### 변경 후
```python
class BotStatus(Base):
    user_id: int
    strategy_id: int (Deprecated - 하위 호환성 유지)
    is_running: bool
    symbol: str
    active_strategies: JSON  # 새로 추가
    # 예시: [
    #   {"strategy_id": 3, "balance_percent": 40, "priority": 1},
    #   {"strategy_id": 5, "balance_percent": 30, "priority": 2}
    # ]
```

### 2. Trade 테이블 수정

#### 변경 전
```python
class Trade(Base):
    user_id: int
    symbol: str
    side: str
    size: float
    price: float
    pnl: float
    # strategy_id 없음
```

#### 변경 후
```python
class Trade(Base):
    user_id: int
    strategy_id: int  # 새로 추가 (어느 전략이 실행한 거래인지 추적)
    symbol: str
    side: str
    size: float
    price: float
    pnl: float
```

### 3. Alembic Migration 작성

**파일**: `backend/alembic/versions/xxxx_add_multi_strategy_support.py`

```python
"""add multi-strategy support

Revision ID: xxxx
Revises: b1c2d3e4f5g6
Create Date: 2025-12-09
"""

def upgrade():
    # BotStatus에 active_strategies JSON 컬럼 추가
    op.add_column('bot_status',
        sa.Column('active_strategies', sa.JSON(), nullable=True))

    # Trade에 strategy_id 컬럼 추가
    op.add_column('trades',
        sa.Column('strategy_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_trade_strategy', 'trades', 'strategies',
        ['strategy_id'], ['id'])

def downgrade():
    op.drop_constraint('fk_trade_strategy', 'trades', type_='foreignkey')
    op.drop_column('trades', 'strategy_id')
    op.drop_column('bot_status', 'active_strategies')
```

---

## 🔧 백엔드 변경

### 1. API 엔드포인트 수정

#### `/bot/start` - 봇 시작
**변경 전**:
```python
{
  "strategy_id": 3
}
```

**변경 후**:
```python
{
  "strategies": [
    {"strategy_id": 3, "balance_percent": 40},
    {"strategy_id": 5, "balance_percent": 30},
    {"strategy_id": 7, "balance_percent": 30}
  ]
}
```

**검증 로직**:
```python
# 1. 총 비율이 100% 이하인지 확인
total_percent = sum(s['balance_percent'] for s in strategies)
if total_percent > 100:
    raise HTTPException(400, "총 잔고 비율이 100%를 초과할 수 없습니다")

# 2. 각 비율이 최소 10% 이상인지 확인
for s in strategies:
    if s['balance_percent'] < 10:
        raise HTTPException(400, "각 전략은 최소 10% 이상 할당해야 합니다")

# 3. 전략 ID가 유효한지 확인
for s in strategies:
    strategy = await session.get(Strategy, s['strategy_id'])
    if not strategy or strategy.user_id != user_id:
        raise HTTPException(404, f"전략 ID {s['strategy_id']}를 찾을 수 없습니다")
```

#### `/bot/add-strategy` - 실행 중 전략 추가 (NEW)
```python
POST /bot/add-strategy
{
  "strategy_id": 8,
  "balance_percent": 20
}
```
**조건**: 봇이 중지 상태일 때만 가능

#### `/bot/remove-strategy` - 전략 제거 (NEW)
```python
POST /bot/remove-strategy
{
  "strategy_id": 3
}
```
**조건**: 봇이 중지 상태일 때만 가능

#### `/bot/update-allocation` - 비율 조정 (NEW)
```python
POST /bot/update-allocation
{
  "strategies": [
    {"strategy_id": 3, "balance_percent": 50},
    {"strategy_id": 5, "balance_percent": 50}
  ]
}
```
**조건**: 봇이 중지 상태일 때만 가능

#### `/bot/status` - 봇 상태 조회 (수정)
**응답 변경**:
```python
# 변경 전
{
  "is_running": true,
  "strategy_id": 3,
  "strategy_name": "공격적 스캘핑"
}

# 변경 후
{
  "is_running": true,
  "active_strategies": [
    {
      "strategy_id": 3,
      "strategy_name": "공격적 스캘핑",
      "balance_percent": 40,
      "allocated_usdt": 34.58,  # 계산값: 86.45 * 0.4
      "priority": 1,
      "current_pnl": 0,  # 이 전략의 누적 손익
      "trade_count": 0   # 이 전략의 거래 수
    },
    {
      "strategy_id": 5,
      "strategy_name": "안정적 스윙",
      "balance_percent": 30,
      "allocated_usdt": 25.94,
      "priority": 2,
      "current_pnl": 0,
      "trade_count": 0
    }
  ],
  "total_balance_used": 70,  # 70%
  "remaining_balance": 30    # 30%
}
```

### 2. bot_runner.py 수정

#### 핵심 변경사항

**파일**: `backend/src/services/bot_runner.py`

```python
class BotRunner:
    def __init__(self):
        self.active_bots: Dict[int, asyncio.Task] = {}
        self.user_strategies: Dict[int, List[Dict]] = {}  # 새로 추가
        # user_id -> [{"strategy_id": 3, "balance_percent": 40}, ...]

    async def start_bot(self, user_id: int, strategies: List[Dict]):
        """
        다중 전략 봇 시작

        Args:
            user_id: 사용자 ID
            strategies: [{"strategy_id": 3, "balance_percent": 40}, ...]
        """
        # 1. 검증 (총 비율, 최소 비율, 전략 존재 여부)
        await self._validate_strategies(user_id, strategies)

        # 2. BotStatus 업데이트
        async with AsyncSessionLocal() as session:
            bot_status = await self._get_or_create_bot_status(session, user_id)
            bot_status.active_strategies = strategies
            bot_status.is_running = True
            await session.commit()

        # 3. 메모리에 전략 목록 저장
        self.user_strategies[user_id] = strategies

        # 4. 봇 태스크 시작
        task = asyncio.create_task(self._run_multi_strategy_bot(user_id))
        self.active_bots[user_id] = task

        logger.info(f"Started multi-strategy bot for user {user_id} with {len(strategies)} strategies")

    async def _run_multi_strategy_bot(self, user_id: int):
        """다중 전략 봇 실행 루프"""
        while user_id in self.active_bots:
            try:
                # 1. 시장 데이터 수신 (공통)
                market_data = await self._get_market_data(user_id)

                # 2. 각 전략마다 시그널 생성 (병렬 처리)
                strategies = self.user_strategies[user_id]
                signal_tasks = [
                    self._process_strategy_signal(
                        user_id,
                        strategy['strategy_id'],
                        strategy['balance_percent'],
                        market_data
                    )
                    for strategy in strategies
                ]
                await asyncio.gather(*signal_tasks, return_exceptions=True)

                # 3. 다음 틱까지 대기
                await asyncio.sleep(5)

            except Exception as e:
                logger.error(f"Error in multi-strategy bot for user {user_id}: {e}")
                await asyncio.sleep(5)

    async def _process_strategy_signal(
        self,
        user_id: int,
        strategy_id: int,
        balance_percent: float,
        market_data: Dict
    ):
        """개별 전략 시그널 처리"""
        try:
            # 1. 전략 로드
            strategy = await self._load_strategy(user_id, strategy_id)

            # 2. 시그널 생성
            signal = await strategy.generate_signal(market_data)

            # 3. 시그널 처리 (buy/sell/hold)
            if signal['action'] in ['buy', 'sell']:
                # 4. 이 전략에 할당된 잔고 계산
                available_balance = await self._get_available_balance(user_id)
                strategy_balance = available_balance * (balance_percent / 100)

                # 5. 주문 크기 계산
                size_metadata = signal.get('size_metadata')
                if size_metadata:
                    position_size_percent = size_metadata['position_size_percent']
                    leverage = size_metadata['leverage']

                    position_value_usdt = strategy_balance * position_size_percent * leverage
                    order_size = position_value_usdt / market_data['price']

                    # 최소 크기 검증
                    if order_size < 0.001:
                        order_size = 0.001

                    logger.info(
                        f"Strategy {strategy_id}: {signal['action']} {order_size:.6f} BTC "
                        f"(allocated: ${strategy_balance:.2f}, {balance_percent}%)"
                    )

                    # 6. 주문 실행
                    trade = await self._execute_order(
                        user_id=user_id,
                        strategy_id=strategy_id,  # 중요: 어느 전략인지 기록
                        signal=signal,
                        size=order_size
                    )

                    # 7. 텔레그램 알림
                    await self._send_telegram_notification(
                        user_id,
                        strategy_id,
                        trade
                    )

        except Exception as e:
            logger.error(f"Error processing strategy {strategy_id} for user {user_id}: {e}")

    async def _execute_order(
        self,
        user_id: int,
        strategy_id: int,  # 새로 추가
        signal: Dict,
        size: float
    ) -> Trade:
        """주문 실행 및 DB 저장"""
        # ... 기존 로직 ...

        # Trade 객체 생성 시 strategy_id 포함
        trade = Trade(
            user_id=user_id,
            strategy_id=strategy_id,  # 새로 추가
            symbol=signal['symbol'],
            side=signal['action'],
            size=size,
            price=signal['price'],
            # ...
        )

        return trade
```

### 3. 전략별 성과 추적

**파일**: `backend/src/api/bot.py`

```python
@router.get("/strategy-performance")
async def get_strategy_performance(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """전략별 성과 조회"""

    # 각 전략의 거래 내역 조회
    result = await session.execute(
        select(
            Trade.strategy_id,
            func.count(Trade.id).label('trade_count'),
            func.sum(Trade.pnl).label('total_pnl'),
            func.avg(Trade.pnl).label('avg_pnl')
        )
        .where(Trade.user_id == current_user.id)
        .where(Trade.strategy_id.isnot(None))
        .group_by(Trade.strategy_id)
    )

    performance_data = []
    for row in result:
        strategy = await session.get(Strategy, row.strategy_id)
        performance_data.append({
            "strategy_id": row.strategy_id,
            "strategy_name": strategy.name,
            "trade_count": row.trade_count,
            "total_pnl": float(row.total_pnl or 0),
            "avg_pnl": float(row.avg_pnl or 0),
            "win_rate": await _calculate_win_rate(session, row.strategy_id)
        })

    return performance_data
```

---

## 🎨 프론트엔드 변경

### 1. Trading.jsx 완전 리팩토링

#### 현재 UI
```
┌─────────────────────────────┐
│ 전략 선택: [드롭다운]       │
│ [시작] [중지]               │
└─────────────────────────────┘
```

#### 변경 후 UI
```
┌──────────────────────────────────────────────────┐
│ 🤖 활성 전략 봇                                  │
│ 총 잔고 사용: 70% | 사용 가능: 30%               │
├──────────────────────────────────────────────────┤
│                                                   │
│ ✅ 🔥 공격적 스캘핑                              │
│    잔고: 40% ($34.58) | 손익: +$0.00 | 거래: 0회 │
│    [비율 조정] [중지]                            │
│                                                   │
│ ✅ 📊 안정적 스윙                                │
│    잔고: 30% ($25.94) | 손익: +$0.00 | 거래: 0회 │
│    [비율 조정] [중지]                            │
│                                                   │
├──────────────────────────────────────────────────┤
│ ➕ 전략 추가 (남은 잔고: 30%)                    │
│                                                   │
│ [드롭다운: 전략 선택]  비율: [20]% [추가]       │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│ 📊 전략별 성과 비교                              │
├──────────────────────────────────────────────────┤
│ [차트: 전략별 수익률 비교]                       │
└──────────────────────────────────────────────────┘

[전체 중지] [전체 시작]
```

### 2. 컴포넌트 구조

**파일**: `frontend/src/pages/Trading.jsx`

```jsx
function Trading() {
  const [activeStrategies, setActiveStrategies] = useState([]);
  const [availableStrategies, setAvailableStrategies] = useState([]);
  const [totalBalance, setTotalBalance] = useState(0);
  const [usedPercent, setUsedPercent] = useState(0);
  const [strategyPerformance, setStrategyPerformance] = useState([]);

  // 봇 상태 조회
  const fetchBotStatus = async () => {
    const response = await fetch('/bot/status', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await response.json();
    setActiveStrategies(data.active_strategies || []);
    setUsedPercent(data.total_balance_used || 0);
  };

  // 전략 추가
  const handleAddStrategy = async (strategyId, balancePercent) => {
    // 1. 검증: 총 비율이 100% 이하인지
    if (usedPercent + balancePercent > 100) {
      message.error('총 잔고 비율이 100%를 초과할 수 없습니다');
      return;
    }

    // 2. API 호출
    await fetch('/bot/add-strategy', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ strategy_id: strategyId, balance_percent: balancePercent })
    });

    // 3. 상태 갱신
    fetchBotStatus();
  };

  // 전략 제거
  const handleRemoveStrategy = async (strategyId) => {
    await fetch('/bot/remove-strategy', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ strategy_id: strategyId })
    });
    fetchBotStatus();
  };

  // 비율 조정
  const handleUpdateAllocation = async (strategyId, newPercent) => {
    // ... 구현
  };

  return (
    <div>
      {/* 활성 전략 목록 */}
      <Card title="🤖 활성 전략 봇">
        <div>
          총 잔고 사용: {usedPercent}% | 사용 가능: {100 - usedPercent}%
        </div>

        {activeStrategies.map(strategy => (
          <StrategyCard
            key={strategy.strategy_id}
            strategy={strategy}
            onRemove={handleRemoveStrategy}
            onUpdatePercent={handleUpdateAllocation}
          />
        ))}

        {/* 전략 추가 폼 */}
        <StrategyAddForm
          availableStrategies={availableStrategies}
          remainingPercent={100 - usedPercent}
          onAdd={handleAddStrategy}
        />
      </Card>

      {/* 전략별 성과 */}
      <Card title="📊 전략별 성과 비교">
        <StrategyPerformanceChart data={strategyPerformance} />
      </Card>
    </div>
  );
}
```

### 3. 새로운 컴포넌트

#### StrategyCard.jsx
```jsx
function StrategyCard({ strategy, onRemove, onUpdatePercent }) {
  const [isEditing, setIsEditing] = useState(false);
  const [newPercent, setNewPercent] = useState(strategy.balance_percent);

  return (
    <div className="strategy-card">
      <div className="strategy-header">
        <span className="strategy-icon">{strategy.strategy_name.split(' ')[0]}</span>
        <span className="strategy-name">{strategy.strategy_name}</span>
      </div>

      <div className="strategy-stats">
        <div>잔고: {strategy.balance_percent}% (${strategy.allocated_usdt.toFixed(2)})</div>
        <div>손익: <span className={strategy.current_pnl >= 0 ? 'profit' : 'loss'}>
          ${strategy.current_pnl.toFixed(2)}
        </span></div>
        <div>거래: {strategy.trade_count}회</div>
      </div>

      <div className="strategy-actions">
        {isEditing ? (
          <>
            <InputNumber
              value={newPercent}
              onChange={setNewPercent}
              min={10}
              max={100}
              formatter={v => `${v}%`}
            />
            <Button onClick={() => {
              onUpdatePercent(strategy.strategy_id, newPercent);
              setIsEditing(false);
            }}>저장</Button>
            <Button onClick={() => setIsEditing(false)}>취소</Button>
          </>
        ) : (
          <>
            <Button onClick={() => setIsEditing(true)}>비율 조정</Button>
            <Button danger onClick={() => onRemove(strategy.strategy_id)}>중지</Button>
          </>
        )}
      </div>
    </div>
  );
}
```

#### StrategyAddForm.jsx
```jsx
function StrategyAddForm({ availableStrategies, remainingPercent, onAdd }) {
  const [selectedStrategy, setSelectedStrategy] = useState(null);
  const [balancePercent, setBalancePercent] = useState(20);

  const handleAdd = () => {
    if (!selectedStrategy) {
      message.error('전략을 선택해주세요');
      return;
    }

    if (balancePercent < 10) {
      message.error('최소 10% 이상 할당해야 합니다');
      return;
    }

    if (balancePercent > remainingPercent) {
      message.error(`남은 잔고(${remainingPercent}%)를 초과할 수 없습니다`);
      return;
    }

    onAdd(selectedStrategy, balancePercent);
    setSelectedStrategy(null);
    setBalancePercent(20);
  };

  return (
    <div className="strategy-add-form">
      <h4>➕ 전략 추가 (남은 잔고: {remainingPercent}%)</h4>

      <Select
        placeholder="전략 선택"
        value={selectedStrategy}
        onChange={setSelectedStrategy}
        style={{ width: 300 }}
      >
        {availableStrategies.map(s => (
          <Select.Option key={s.id} value={s.id}>
            {s.name}
          </Select.Option>
        ))}
      </Select>

      <InputNumber
        value={balancePercent}
        onChange={setBalancePercent}
        min={10}
        max={remainingPercent}
        formatter={v => `${v}%`}
      />

      <Button type="primary" onClick={handleAdd}>추가</Button>
    </div>
  );
}
```

#### StrategyPerformanceChart.jsx
```jsx
import { Line } from '@ant-design/charts';

function StrategyPerformanceChart({ data }) {
  // data: [
  //   { strategy_name: "공격적 스캘핑", total_pnl: 12.5, trade_count: 45, win_rate: 65 },
  //   { strategy_name: "안정적 스윙", total_pnl: 8.3, trade_count: 20, win_rate: 80 }
  // ]

  const config = {
    data: data,
    xField: 'strategy_name',
    yField: 'total_pnl',
    point: {
      size: 5,
      shape: 'diamond',
    },
    label: {
      style: {
        fill: '#aaa',
      },
    },
  };

  return (
    <div>
      <h4>전략별 누적 수익</h4>
      <Line {...config} />

      <table className="performance-table">
        <thead>
          <tr>
            <th>전략</th>
            <th>거래 수</th>
            <th>총 손익</th>
            <th>평균 손익</th>
            <th>승률</th>
          </tr>
        </thead>
        <tbody>
          {data.map(s => (
            <tr key={s.strategy_name}>
              <td>{s.strategy_name}</td>
              <td>{s.trade_count}</td>
              <td className={s.total_pnl >= 0 ? 'profit' : 'loss'}>
                ${s.total_pnl.toFixed(2)}
              </td>
              <td>${s.avg_pnl.toFixed(2)}</td>
              <td>{s.win_rate.toFixed(1)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

---

## 🧪 테스트 시나리오

### 1. 기본 시나리오
1. 사용자가 3개 전략 추가 (40% + 30% + 30%)
2. 봇 시작
3. 각 전략이 독립적으로 시그널 생성
4. BTC 가격이 하락하여 전략 A는 롱, 전략 B는 숏 시그널 생성
5. 두 거래 모두 실행되며, 각각 strategy_id가 기록됨
6. 전략별 성과 조회 시 개별 손익 확인 가능

### 2. 에러 시나리오
1. 총 비율이 100% 초과 시도 → 400 에러
2. 10% 미만 할당 시도 → 400 에러
3. 존재하지 않는 전략 ID → 404 에러
4. 다른 사용자의 전략 사용 시도 → 403 에러

### 3. 잔고 부족 시나리오
1. 전략 A(40%), B(30%), C(30%) 실행
2. 사용 가능 잔고: $80
3. 전략 A에 할당: $32
4. 전략 B에 할당: $24
5. 전략 C에 할당: $24
6. 동시에 3개 전략이 매수 시그널 생성
7. 우선순위 순서로 실행 (A → B → C)
8. 잔고 부족 시 나중 전략은 최소 크기(0.001 BTC)로 주문

---

## 📅 구현 순서

### Phase 1: 데이터베이스 및 백엔드 기초 (2-3시간)
1. ✅ Alembic migration 작성 및 실행
2. ✅ BotStatus 모델 수정
3. ✅ Trade 모델 수정
4. ✅ 기존 데이터 마이그레이션 스크립트 작성

### Phase 2: 백엔드 API 개발 (3-4시간)
1. ✅ `/bot/start` 엔드포인트 수정 (다중 전략 지원)
2. ✅ `/bot/add-strategy` 구현
3. ✅ `/bot/remove-strategy` 구현
4. ✅ `/bot/update-allocation` 구현
5. ✅ `/bot/status` 응답 수정
6. ✅ `/strategy-performance` 구현

### Phase 3: BotRunner 로직 개발 (4-5시간)
1. ✅ `start_bot()` 다중 전략 지원
2. ✅ `_run_multi_strategy_bot()` 구현
3. ✅ `_process_strategy_signal()` 구현
4. ✅ 전략별 잔고 할당 로직
5. ✅ `_execute_order()` strategy_id 추가
6. ✅ 텔레그램 알림 수정 (전략 이름 포함)

### Phase 4: 프론트엔드 개발 (4-5시간)
1. ✅ Trading.jsx 리팩토링
2. ✅ StrategyCard 컴포넌트
3. ✅ StrategyAddForm 컴포넌트
4. ✅ StrategyPerformanceChart 컴포넌트
5. ✅ CSS 스타일링

### Phase 5: 테스트 및 배포 (2-3시간)
1. ✅ 로컬 테스트 (기본 시나리오)
2. ✅ 에러 시나리오 테스트
3. ✅ 서버 배포
4. ✅ 실제 계정으로 통합 테스트

**총 예상 시간**: 15-20시간

---

## 🚨 주의사항

### 1. 하위 호환성
- 기존 `strategy_id` 필드는 유지 (마이그레이션 시 첫 번째 전략으로 설정)
- 기존 API도 당분간 지원 (deprecated 표시)

### 2. 성능 최적화
- 각 전략의 시그널 생성을 병렬 처리 (`asyncio.gather`)
- API Rate Limit 준수 (잔고 조회는 전체 1회, 전략별로 재사용)

### 3. 에러 처리
- 한 전략의 에러가 다른 전략에 영향을 주지 않도록 `return_exceptions=True`
- 잔고 부족 시 graceful degradation (최소 크기로 주문)

### 4. 보안
- 사용자는 자신의 전략만 사용 가능하도록 검증
- 총 비율 100% 제한은 서버 측에서도 검증 (클라이언트 검증만 믿지 말 것)

---

## 📝 추가 고려사항

### 향후 개선 가능 항목 (Phase 2)
1. 실행 중 비율 실시간 조정
2. 전략 간 시그널 조율 (같은 심볼에서 롱/숏 동시 발생 시 상쇄)
3. 전략별 리스크 관리 (개별 손절/익절 설정)
4. 전략 자동 재분배 (성과 좋은 전략에 더 많은 비율 자동 할당)
5. 백테스팅 기능 (여러 전략 조합의 과거 성과 시뮬레이션)

---

## 🎯 성공 지표

구현 완료 후 다음 사항들이 가능해야 합니다:

- ✅ 사용자가 최대 5개 전략을 동시에 실행
- ✅ 각 전략에 10-100% 범위의 잔고 비율 할당
- ✅ 총 비율이 100%를 초과하지 않음
- ✅ 각 전략이 독립적으로 시그널 생성 및 거래 실행
- ✅ 전략별 손익 추적 및 성과 비교
- ✅ 실시간 전략 추가/제거/비율 조정 (봇 중지 상태)
- ✅ API Rate Limit 준수 (기존 최적화 유지)
- ✅ 에러 발생 시 다른 전략에 영향 없음

---

## 📞 문의 및 피드백

구현 중 질문이나 방향성 변경이 필요하면 언제든지 말씀해주세요!
