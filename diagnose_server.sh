#!/bin/bash
"""
배포된 서버 진단 스크립트
: 봇 실행, 진입, 텔레그램 알림 테스트

사용법:
1. 서버에 SSH 접속
2. cd /path/to/auto-dashboard
3. bash diagnose_server.sh
"""

echo "=========================================="
echo "🔍 서버 진단 시작 ($(date))"
echo "=========================================="

echo ""
echo "1. 🐳 Docker 컨테이너 상태 확인"
echo "-----------------------------------------"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "2. 📋 백엔드 로그 (최근 50줄)"
echo "-----------------------------------------"
docker logs trading-backend --tail 50

echo ""
echo "3. 🔍 봇 관련 로그 필터링"
echo "-----------------------------------------"
docker logs trading-backend 2>&1 | grep -i "bot\|strategy\|signal\|trade\|position\|telegram" | tail -30

echo ""
echo "4. 🌐 API 헬스체크"
echo "-----------------------------------------"
curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || echo "❌ Health check failed"

echo ""
echo "5. 📊 데이터베이스 전략 확인"
echo "-----------------------------------------"
docker exec -it trading-postgres psql -U trading_user -d trading_prod -c "SELECT id, name, code, is_active FROM strategies LIMIT 10;"

echo ""
echo "6. 📊 데이터베이스 봇 상태 확인"
echo "-----------------------------------------"
docker exec -it trading-postgres psql -U trading_user -d trading_prod -c "SELECT user_id, strategy_id, is_running FROM bot_status;"

echo ""
echo "7. 🔑 API 키 설정 확인"
echo "-----------------------------------------"
docker exec -it trading-postgres psql -U trading_user -d trading_prod -c "SELECT user_id, LENGTH(encrypted_api_key) as api_key_len FROM api_keys;"

echo ""
echo "8. 📱 텔레그램 설정 확인"
echo "-----------------------------------------"
docker exec trading-backend bash -c 'echo "TELEGRAM_BOT_TOKEN: ${TELEGRAM_BOT_TOKEN:0:10}..."'
docker exec trading-backend bash -c 'echo "TELEGRAM_CHAT_ID: $TELEGRAM_CHAT_ID"'

echo ""
echo "=========================================="
echo "✅ 진단 완료"
echo "=========================================="
