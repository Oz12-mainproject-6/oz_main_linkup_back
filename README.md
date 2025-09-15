# 🎭 OZ LinkUp - 아이돌 캘린더 서비스

K-Pop 아이돌 팬들을 위한 종합 캘린더 및 커뮤니티 플랫폼입니다.

## 📋 서비스 개요

### 주요 기능
- **🏢 소속사 계정**: 아티스트 등록 및 이벤트 관리
- **👥 팬 계정**: 아티스트 구독 및 팬 커뮤니티 참여
- **📅 이벤트 캘린더**: 콘서트, 팬사인회, 음원 발매 등 다양한 이벤트
- **🔔 알림 시스템**: 이벤트 등록 즉시 + 1시간 전 알림
- **📝 팬 포스트**: 구독한 아티스트 관련 팬 커뮤니티
- **🖼️ 이미지 공유**: 소속사 공식 이미지를 팬 포스트에서 활용

### 사용자 유형
1. **소속사**: 아티스트 관리, 이벤트 등록, 공식 이미지 업로드
2. **팬**: 아티스트 구독, 팬 포스트 작성, 커뮤니티 참여

## 🏗️ 기술 스택

- **Backend**: FastAPI (Python 3.12+)
- **Database**: PostgreSQL + Tortoise ORM
- **Authentication**: JWT + OAuth2 (카카오, 네이버, 구글)
- **Storage**: AWS S3 (이미지 업로드)
- **Notifications**: FCM (Push), Email
- **Background Tasks**: Celery + Redis
- **Deployment**: Docker + Docker Compose

## 🚀 개발 환경 설정

### 1. 사전 요구사항
```bash
# Python 3.12+
python --version

# uv 패키지 매니저 설치
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. 프로젝트 설정
```bash
# 저장소 클론
git clone <repository-url>
cd oz_main_linkup_back

# 개발 환경 의존성 설치
uv sync --extra dev

# 환경변수 설정
cp .env.example .env
# .env 파일 편집하여 실제 값 입력
```

### 3. 데이터베이스 설정
```bash
# PostgreSQL 실행 (Docker Compose)
docker compose up -d db

# 데이터베이스 마이그레이션
aerich init -t app.config.TORTOISE_ORM
aerich init-db
aerich migrate
aerich upgrade
```

### 4. 개발 서버 실행
```bash
# FastAPI 개발 서버 시작
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 또는 전체 서비스 실행 (Docker Compose)
docker compose up --build
```

## 🐳 Docker 환경 실행

### 전체 서비스 실행
```bash
# 모든 서비스 실행 (DB, Redis, App)
docker compose up --build

# 백그라운드 실행
docker compose up -d --build
```

### 개별 서비스 실행
```bash
# 데이터베이스만 실행
docker compose up -d db

# Redis만 실행
docker compose up -d redis
```

## 📁 프로젝트 구조

```
app/
├── core/                    # 핵심 기능
│   ├── mixins.py           # TimestampMixin
│   ├── s3.py               # AWS S3 핸들러
│   ├── database.py         # DB 연결
│   └── exceptions.py       # 예외 처리
├── features/               # Feature 기반 모듈
│   ├── users/              # 사용자 & 소속사
│   ├── artists/            # 아티스트 관리
│   ├── events/             # 이벤트 관리
│   ├── posts/              # 팬 포스트 & 커뮤니티
│   ├── images/             # 이미지 관리 & 공유
│   └── notifications/      # 알림 & 구독
├── shared/                 # 공통 유틸리티
├── config.py              # 설정
└── main.py                # FastAPI 앱
```

## 🔑 환경변수 설정

`.env` 파일에 다음 값들을 설정하세요:

```bash
# Database
POSTGRES_DB=linkup
POSTGRES_USER=linkup
POSTGRES_PASSWORD=linkup
DB_HOST=localhost
DB_PORT=5432

# AWS S3
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=ap-northeast-2
AWS_S3_BUCKET=your_bucket_name

# JWT
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Social Login
KAKAO_CLIENT_ID=your_kakao_client_id
KAKAO_CLIENT_SECRET=your_kakao_client_secret
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Notifications
FCM_SERVER_KEY=your_fcm_server_key
MAIL_USERNAME=your_email
MAIL_PASSWORD=your_email_password

# Redis
REDIS_URL=redis://localhost:6379
```

## 🧪 테스트

```bash
# 테스트 실행
pytest

# 커버리지와 함께 테스트
pytest --cov=app --cov-report=html

# 특정 테스트 파일만 실행
pytest tests/test_users.py -v
```

## 📖 API 문서

개발 서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔧 개발 도구

```bash
# 코드 포맷팅
ruff format .

# 린팅
ruff check .

# 타입 체킹
mypy app/

# Pre-commit 훅 설치
pre-commit install
```

## 📊 ERD (Entity Relationship Diagram)


