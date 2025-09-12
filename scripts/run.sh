#!/bin/sh
set -e

echo "Starting application..."

# 데이터베이스 연결 대기
echo "Waiting for database connection..."
while ! nc -z db 5432; do
  sleep 1
done
echo "Database is ready!"

# 마이그레이션 수행
echo "Running database migrations..."
export DB_HOST=db
# 초기 마이그레이션이 없으면 생성
uv run aerich init-db 2>/dev/null || echo "Database already initialized"
uv run aerich upgrade

# FastAPI 앱 실행
echo "Starting FastAPI application..."
if [ "$ENVIRONMENT" = "production" ]; then
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
else
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
fi