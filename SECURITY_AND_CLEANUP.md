# 🔐 보안 가이드 및 프로젝트 정리 보고서

> **작성일**: 2025-12-09  
> **목적**: 프로젝트 구조 정리 및 보안 강화

---

## 📁 정리된 프로젝트 구조

```
auto-dashboard/
├── 📂 backend/                 # 백엔드 API 서버
│   ├── src/
│   │   ├── api/               # API 엔드포인트
│   │   ├── database/          # DB 모델 및 연결
│   │   ├── schemas/           # Pydantic 스키마
│   │   ├── services/          # 비즈니스 로직
│   │   │   ├── bitget_rest.py    # Bitget API 클라이언트
│   │   │   ├── bot_runner.py     # 트레이딩 봇 실행기
│   │   │   ├── strategy_loader.py # 전략 로더
│   │   │   └── telegram/         # 텔레그램 알림
│   │   ├── strategies/        # 트레이딩 전략
│   │   └── utils/             # 유틸리티
│   ├── alembic/               # DB 마이그레이션
│   ├── scripts/               # 백엔드 스크립트
│   ├── requirements.txt       # Python 의존성
│   └── Dockerfile            # 백엔드 Docker 설정
│
├── 📂 frontend/               # 프론트엔드 (React + Vite)
│   ├── src/
│   │   ├── components/       # UI 컴포넌트
│   │   ├── pages/            # 페이지 컴포넌트
│   │   ├── services/         # API 서비스
│   │   └── stores/           # 상태 관리
│   └── Dockerfile            # 프론트엔드 Docker 설정
│
├── 📂 admin-frontend/         # 관리자 프론트엔드
│
├── 📂 docs/                   # 문서
│   ├── archive/              # 아카이브된 개발 문서
│   └── README.md             # 메인 문서
│
├── 📂 scripts/                # 배포/디버그 스크립트
│   ├── deploy.sh             # 배포 스크립트
│   ├── deploy-to-server.sh   # 서버 배포
│   └── debug-*.sh            # 디버그 스크립트
│
├── 📂 nginx/                  # Nginx 설정
├── 📂 monitoring/             # 모니터링 설정
│
├── 📄 docker-compose.yml      # Docker 컴포즈 설정
├── 📄 .env.example            # 환경변수 예시
├── 📄 .gitignore              # Git 제외 파일
└── 📄 README.md               # 프로젝트 설명
```

---

## 🔐 보안 체크리스트

### ✅ 환경변수 보안

| 항목 | 상태 | 설명 |
|------|------|------|
| `.env` 파일 gitignore | ✅ 완료 | 민감 정보 Git 제외 |
| API 키 암호화 저장 | ✅ 완료 | `ENCRYPTION_KEY`로 AES 암호화 |
| JWT 시크릿 설정 | ✅ 완료 | 별도 `JWT_SECRET` 사용 |
| 프로덕션 비밀번호 변경 | ⚠️ 권장 | 아래 권장사항 참고 |

### ✅ 서버 보안

| 항목 | 상태 | 설명 |
|------|------|------|
| SSH 비밀번호 인증 | ⚠️ 개선 필요 | SSH 키 인증으로 변경 권장 |
| 방화벽 설정 | ⚠️ 확인 필요 | 필요 포트만 개방 확인 |
| HTTPS 설정 | ❌ 미완료 | SSL 인증서 설치 권장 |
| Docker 보안 | ✅ 완료 | non-root 유저 사용 |

### ✅ 코드 보안

| 항목 | 상태 | 설명 |
|------|------|------|
| SQL Injection 방지 | ✅ 완료 | SQLAlchemy ORM 사용 |
| XSS 방지 | ✅ 완료 | React 기본 이스케이프 |
| CORS 설정 | ✅ 완료 | 허용 도메인 제한 |

---

## 🔧 권장 보안 조치

### 1. 프로덕션 비밀번호 변경 (필수)

```bash
# 서버에서 .env 파일 수정
ssh root@158.247.245.197
cd /root/auto-dashboard
nano .env

# 변경해야 할 항목:
POSTGRES_PASSWORD=<새로운_강력한_비밀번호>
REDIS_PASSWORD=<새로운_강력한_비밀번호>
JWT_SECRET=<새로운_랜덤_문자열>
ENCRYPTION_KEY=<32바이트_랜덤_키>
```

### 2. SSH 키 인증 설정 (권장)

```bash
# 로컬에서 SSH 키 생성
ssh-keygen -t ed25519 -C "your-email@example.com"

# 서버에 공개키 복사
ssh-copy-id -i ~/.ssh/id_ed25519.pub root@158.247.245.197

# 서버에서 비밀번호 인증 비활성화
sudo nano /etc/ssh/sshd_config
# PasswordAuthentication no
sudo systemctl restart sshd
```

### 3. HTTPS 설정 (권장)

```bash
# Let's Encrypt 무료 SSL 인증서
apt install certbot python3-certbot-nginx
certbot --nginx -d yourdomain.com
```

### 4. 방화벽 설정 (권장)

```bash
# UFW 설치 및 설정
apt install ufw
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
ufw enable
```

---

## 📦 Git 동기화 가이드

### 로컬에서 서버로 동기화

```bash
# 1. 변경사항 커밋
cd /Users/mr.joo/Desktop/auto-dashboard
git add .
git commit -m "프로젝트 구조 정리 및 보안 강화"
git push origin main

# 2. 서버에서 Pull
ssh root@158.247.245.197
cd /root/auto-dashboard
git pull origin main

# 3. Docker 재빌드
docker compose build
docker compose up -d
```

### 서버 직접 배포 (rsync)

```bash
# 백엔드만 동기화
rsync -avz --exclude 'node_modules' --exclude '__pycache__' --exclude '.git' \
  /Users/mr.joo/Desktop/auto-dashboard/backend/ \
  root@158.247.245.197:/root/auto-dashboard/backend/

# 프론트엔드만 동기화
rsync -avz --exclude 'node_modules' --exclude '.git' \
  /Users/mr.joo/Desktop/auto-dashboard/frontend/ \
  root@158.247.245.197:/root/auto-dashboard/frontend/
```

---

## 🚀 빠른 배포 명령어

### 백엔드 업데이트

```bash
# 로컬에서
sshpass -p 'YOUR_PASSWORD' rsync -avz \
  /Users/mr.joo/Desktop/auto-dashboard/backend/src/ \
  root@158.247.245.197:/root/auto-dashboard/backend/src/

# 서버에서
ssh root@158.247.245.197 "cd /root/auto-dashboard && docker compose build backend && docker compose up -d backend"
```

### 프론트엔드 업데이트

```bash
# 로컬에서
sshpass -p 'YOUR_PASSWORD' rsync -avz \
  /Users/mr.joo/Desktop/auto-dashboard/frontend/src/ \
  root@158.247.245.197:/root/auto-dashboard/frontend/src/

# 서버에서
ssh root@158.247.245.197 "cd /root/auto-dashboard && docker compose build frontend && docker compose up -d frontend"
```

---

## 📋 현재 서비스 상태

### 서버 정보

- **IP**: 158.247.245.197
- **프론트엔드**: <http://158.247.245.197:3000>
- **백엔드 API**: <http://158.247.245.197:8000>
- **API 문서**: <http://158.247.245.197:8000/docs>

### Docker 컨테이너

| 컨테이너 | 포트 | 상태 |
|----------|------|------|
| trading-backend | 8000 | ✅ Running |
| trading-frontend | 3000 | ✅ Running |
| trading-postgres | 5432 | ✅ Running |
| trading-redis | 6379 | ✅ Running |

### 테스트 계정

- **이메일**: <admin@admin.com>
- **비밀번호**: admin123

### Bitget API (테스트용)

- **API Key**: bg_6e5b354a87da274d922680aff9bd3778
- ⚠️ **프로덕션에서는 새 API 키 발급 필요**

### 텔레그램 봇

- **Bot Token**: 8289295080:AAHce1EwlO6O33YbTHps_oaUHo7YJ4MBrso
- **Chat ID**: 7980845952

---

## 🧹 정리된 항목

### 이동된 문서 (docs/archive/)

- 40+ 개발 문서가 `docs/archive/`로 이동
- 핵심 문서만 루트에 유지 (README.md)

### 이동된 스크립트 (scripts/)

- 배포 및 디버그 스크립트가 `scripts/`로 이동

### 삭제된 파일

- `__pycache__/` 캐시 디렉토리
- `.pyc` 컴파일된 Python 파일
- `.DS_Store` macOS 시스템 파일
- `backend/trading.db` 로컬 테스트 DB

---

## ⚠️ 주의사항

### 절대 Git에 커밋하지 말 것

- `.env` 파일 (API 키, 비밀번호 포함)
- `*.pem` 인증서 파일
- 로그 파일 (`*.log`)

### 프로덕션 배포 전 확인

1. 모든 테스트 API 키를 프로덕션용으로 교체
2. 강력한 비밀번호로 변경
3. HTTPS 설정
4. 백업 정책 수립

---

## 📞 문의

문제 발생 시 다음을 확인하세요:

1. Docker 컨테이너 상태: `docker ps`
2. 컨테이너 로그: `docker logs trading-backend --tail 100`
3. 서버 연결: `ping 158.247.245.197`
