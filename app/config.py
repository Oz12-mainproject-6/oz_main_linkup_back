import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()

# Environment detection
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
IS_DEVELOPMENT = ENVIRONMENT == "development"
IS_PRODUCTION = ENVIRONMENT == "production"


# Database configuration - 간소화된 버전
def get_database_config() -> dict[str, Any]:
    """환경에 따른 데이터베이스 설정 반환"""

    # DB 연결 정보
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = int(os.getenv("DB_PORT", "5432"))
    db_user = os.getenv("DB_USER", "linkup")
    db_password = os.getenv("DB_PASSWORD", "linkup")
    db_name = os.getenv("DB_NAME", "linkup")

    # 기본 설정
    config = {
        "engine": "tortoise.backends.asyncpg",
        "credentials": {
            "host": db_host,
            "port": db_port,
            "user": db_user,
            "password": db_password,
            "database": db_name,
        },
    }

    # 프로덕션 환경에서는 추가 설정 (Docker 환경 제외)
    if IS_PRODUCTION and db_host != "db":  # Docker 내부 db 호스트가 아닌 경우만
        config["credentials"].update(
            {
                "ssl": "require",
                "maxsize": int(os.getenv("DB_POOL_SIZE", "20")),
                "minsize": int(os.getenv("DB_POOL_MIN_SIZE", "5")),
            }
        )

    return config


# Tortoise ORM 설정
TORTOISE_ORM = {
    "connections": {"default": get_database_config()},
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
    print(f"📊 Database Host: {os.getenv('DB_HOST', 'localhost')}")
    print(f"🔐 Debug: {DEBUG}")
