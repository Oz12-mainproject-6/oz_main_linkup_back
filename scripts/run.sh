#!/bin/sh
set -e

echo "🚀 Starting application..."

# 데이터베이스 연결 대기
echo "⏳ Waiting for database connection..."
for i in $(seq 1 30); do
    if nc -z db 5432; then
        echo "✅ Database is ready!"
        break
    fi
    echo "Waiting for database... ($i/30)"
    sleep 2
done

if ! nc -z db 5432; then
    echo "❌ Database connection timeout!"
    exit 1
fi

# 환경 변수 설정
export DB_HOST=db

# Aerich 초기화 상태 확인 및 마이그레이션 수행
echo "🔧 Setting up database migrations..."

# aerich 디렉토리가 없으면 초기화
if [ ! -d "migrations" ]; then
    echo "📦 Initializing aerich..."
    # aerich init 버그 수정을 위해 디렉토리 수동 생성
    mkdir -p migrations/models
    uv run aerich init -t app.config.TORTOISE_ORM --location migrations
fi

# 간소화된 마이그레이션 로직
echo "🗄️ Setting up database..."

# aerich이 초기화되지 않았으면 초기화
if ! uv run aerich history >/dev/null 2>&1; then
    echo "🏗️ Initializing database with aerich..."
    uv run aerich init-db
else
    echo "📊 Running migrations..."
    uv run aerich migrate --name "auto_migration" 2>/dev/null || echo "No new migrations needed"
    uv run aerich upgrade 2>/dev/null || echo "No migrations to apply"
fi

echo "✅ Database setup complete!"

# FastAPI 앱 실행
echo "🌟 Starting FastAPI application..."
# Docker에서는 항상 production 모드로 실행 (reload 비활성화)
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2