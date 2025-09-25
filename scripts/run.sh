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
    uv run aerich init -t app.config.TORTOISE_ORM --location migrations
fi

# 데이터베이스가 비어있으면 초기화
echo "🗄️ Checking database state..."
DB_TABLES=$(uv run python -c "
import asyncio
from tortoise import Tortoise
from app.config import TORTOISE_ORM

async def check_tables():
    await Tortoise.init(config=TORTOISE_ORM)
    conn = Tortoise.get_connection('default')
    tables = await conn.execute_query('SELECT table_name FROM information_schema.tables WHERE table_schema = \\'public\\';')
    await Tortoise.close_connections()
    return len(tables[1]) if tables[1] else 0

result = asyncio.run(check_tables())
print(result)
" 2>/dev/null || echo "0")

if [ "$DB_TABLES" = "0" ] || [ "$DB_TABLES" = "" ]; then
    echo "🏗️ Initializing empty database..."
    uv run aerich init-db
else
    echo "📊 Database has tables, running migrations..."
    # 마이그레이션 생성 (변경사항이 있는 경우)
    uv run aerich migrate --name "auto_migration" 2>/dev/null || echo "No new migrations needed"
    # 마이그레이션 적용
    uv run aerich upgrade
fi

echo "✅ Database setup complete!"

# 더미 데이터 생성 (개발 환경에서만, 환경변수로 제어)
if [ "$ENVIRONMENT" = "development" ] && [ "$CREATE_DUMMY_DATA" = "true" ]; then
    echo "🎭 Creating dummy data..."
    uv run python create_dummy_data_fixed.py || echo "⚠️ Dummy data creation failed, continuing..."
fi

# FastAPI 앱 실행
echo "🌟 Starting FastAPI application..."
if [ "$ENVIRONMENT" = "production" ]; then
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
else
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level info
fi