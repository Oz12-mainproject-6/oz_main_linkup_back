# Docker Deployment Guide

## 🚀 Quick Start

### 1. 로컬 개발 (Local Development)

```bash
# 1. 환경 설정
cp .env.example .env  # .env 파일 설정

# 2. 데이터베이스만 실행 (로컬에서 개발할 때)
docker-compose up db -d

# 3. 마이그레이션 실행
uv run aerich upgrade

# 4. 더미 데이터 생성 (선택사항)
uv run python create_dummy_data_fixed.py

# 5. 애플리케이션 실행
uv run uvicorn app.main:app --reload
```

### 2. 전체 Docker 배포 (Full Docker Deployment)

```bash
# 1. .env 파일에서 DATABASE_URL 수정
# 주석 처리: DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/oz_linkup
# 주석 해제: DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/oz_linkup

# 2. 더미 데이터 생성 활성화 (선택사항)
echo "CREATE_DUMMY_DATA=true" >> .env

# 3. Docker Compose 실행
docker-compose up --build

# 4. 로그 확인
docker-compose logs -f app
```

## 📋 환경 변수 설정

### 필수 환경변수

```bash
# Database
POSTGRES_DB=oz_linkup
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password

# Application
ENVIRONMENT=development
DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/oz_linkup

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key-here-change-in-production
```

### 선택적 환경변수

```bash
# 더미 데이터 생성
CREATE_DUMMY_DATA=true

# OAuth (필요시)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
KAKAO_CLIENT_ID=your-kakao-client-id
KAKAO_CLIENT_SECRET=your-kakao-client-secret

# AWS S3 (필요시)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=ap-northeast-2
AWS_S3_BUCKET=your-s3-bucket
```

## 🔧 마이그레이션 관리

### 새로운 마이그레이션 생성

```bash
# 1. 모델 변경 후 마이그레이션 생성
uv run aerich migrate --name "your_migration_name"

# 2. 또는 자동 마이그레이션 생성 스크립트 사용
python generate_migration.py

# 3. 마이그레이션 적용
uv run aerich upgrade
```

### Docker 환경에서 마이그레이션

```bash
# 컨테이너 내부에서 마이그레이션 실행
docker-compose exec app uv run aerich upgrade

# 새로운 마이그레이션 생성
docker-compose exec app uv run aerich migrate --name "your_migration_name"
```

## 🎭 더미 데이터

### 더미 데이터 생성

```bash
# 로컬에서
uv run python create_dummy_data_fixed.py

# Docker에서
docker-compose exec app uv run python create_dummy_data_fixed.py

# 또는 환경변수로 자동 생성 설정
CREATE_DUMMY_DATA=true
```

### 생성되는 데이터

- 관리자 계정: `admin_dummy@admin.com` / `admin123!`
- 회사 계정: `sm_dummy@company.com` / `company123!`
- 팬 계정: `fan_dummy_1@gmail.com` / `fan123!`
- 아티스트, 이벤트, 포스트, 댓글, 좋아요 등

## 🐛 문제 해결

### 1. 데이터베이스 연결 오류

```bash
# 데이터베이스 컨테이너 상태 확인
docker-compose ps db

# 로그 확인
docker-compose logs db

# 재시작
docker-compose restart db
```

### 2. 마이그레이션 오류

```bash
# 마이그레이션 상태 확인
uv run aerich history

# 강제 초기화 (주의: 데이터 손실)
docker-compose down -v  # 볼륨 삭제
docker-compose up --build
```

### 3. 포트 충돌

```bash
# 다른 포트 사용
docker-compose up --build -p 8001:8000
```

## 📊 모니터링

### 로그 확인

```bash
# 실시간 로그
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f app
docker-compose logs -f db
```

### 상태 확인

```bash
# 컨테이너 상태
docker-compose ps

# 리소스 사용량
docker stats
```

## 🚦 API 엔드포인트

서버 시작 후 접근 가능한 엔드포인트:

- API 문서: http://localhost:8000/docs
- 아티스트 목록: http://localhost:8000/api/idol
- 사용자 인증: http://localhost:8000/api/auth
- 이벤트: http://localhost:8000/api/events

## 🔄 프로덕션 배포

프로덕션 환경에서는:

1. `ENVIRONMENT=production` 설정
2. `JWT_SECRET_KEY` 강력한 키로 변경
3. `CREATE_DUMMY_DATA=false` 설정
4. HTTPS 설정
5. 보안 설정 강화

```bash
ENVIRONMENT=production
CREATE_DUMMY_DATA=false
JWT_SECRET_KEY=your-very-secure-production-key-here
```