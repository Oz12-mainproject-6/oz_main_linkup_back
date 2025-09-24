import os
from typing import Dict, Any

from dotenv import load_dotenv

load_dotenv()

# Environment detection
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
IS_DEVELOPMENT = ENVIRONMENT == "development"
IS_PRODUCTION = ENVIRONMENT == "production"
IS_DOCKER = os.getenv("DOCKER", "false").lower() == "true"

# Database configuration based on environment
def get_database_config() -> Dict[str, Any]:
    """환경에 따른 데이터베이스 설정 반환"""
    
    # DATABASE_URL이 있다면 우선 사용 (프로덕션 배포용)
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url
    
    # 개발 환경별 설정
    if IS_DOCKER:
        # Docker Compose 환경
        return {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "host": os.getenv("DB_HOST", "db"),  # Docker service name
                "port": int(os.getenv("DB_PORT", "5432")),
                "user": os.getenv("DB_USER", "linkup"),
                "password": os.getenv("DB_PASSWORD", "linkup"),
                "database": os.getenv("DB_NAME", "linkup"),
            },
        }
    elif IS_DEVELOPMENT:
        # 로컬 개발 환경
        return {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "host": os.getenv("DB_HOST", "localhost"),
                "port": int(os.getenv("DB_PORT", "5432")),
                "user": os.getenv("DB_USER", "linkup"),
                "password": os.getenv("DB_PASSWORD", "linkup"),
                "database": os.getenv("DB_NAME", "linkup"),
            },
        }
    else:
        # 프로덕션 환경 - 보다 엄격한 설정
        return {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "host": os.getenv("DB_HOST"),
                "port": int(os.getenv("DB_PORT", "5432")),
                "user": os.getenv("DB_USER"),
                "password": os.getenv("DB_PASSWORD"),
                "database": os.getenv("DB_NAME"),
                "ssl": "require" if IS_PRODUCTION else None,
                "maxsize": int(os.getenv("DB_POOL_SIZE", "20")),
                "minsize": int(os.getenv("DB_POOL_MIN_SIZE", "5")),
            },
        }

# Tortoise ORM 설정
TORTOISE_ORM = {
    "connections": {
        "default": get_database_config()
    },
    "apps": {
        "models": {
            "models": [
                "aerich.models",
                "app.features.users.models",
                "app.features.artists.models",
                "app.features.events.models",
                "app.features.posts.models",
                "app.features.images.models",
                "app.features.notifications.models",
                "app.features.subscriptions.models",
            ],
            "default_connection": "default",
        }
    },
    "use_tz": True,
    "timezone": "Asia/Seoul",
}

# 로깅 설정
LOG_LEVEL = "DEBUG" if IS_DEVELOPMENT else "INFO"

# CORS 설정
if IS_DEVELOPMENT:
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
else:
    # 프로덕션에서는 정확한 도메인만 허용
    CORS_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")

# 기타 설정
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key" if IS_DEVELOPMENT else None)
DEBUG = IS_DEVELOPMENT

# 설정 요약 출력
if IS_DEVELOPMENT:
    print(f"🌍 Environment: {ENVIRONMENT}")
    print(f"🐳 Docker: {IS_DOCKER}")
    print(f"📊 Database: {type(get_database_config()).__name__}")
    print(f"🔐 Debug: {DEBUG}")
