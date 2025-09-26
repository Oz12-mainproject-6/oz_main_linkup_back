FROM python:3.12-slim

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Python 의존성 파일들 복사
COPY pyproject.toml uv.lock ./


# 의존성 설치
RUN uv sync


# 애플리케이션 코드 복사
COPY . .

# scripts 실행 권한 부여
RUN chmod +x ./scripts/run.sh

# 포트 노출
EXPOSE 8000

# FastAPI 앱 실행 (기본 개발 환경)
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
