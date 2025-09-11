
import os
from dotenv import load_dotenv

load_dotenv()

# Database settings
TORTOISE_ORM = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "host": os.getenv("DB_HOST", "localhost"),
                "port": int(os.getenv("DB_PORT", "5432")),
                "user": os.getenv("DB_USER", "linkup"),
                "password": os.getenv("DB_PASSWORD", "linkup"),
                "database": os.getenv("DB_NAME", "linkup"),
            }
        }
    },
    "apps": {
        "models": {
            "models": ["app.models", "aerich.models"],
            "default_connection": "default",
        }
    }
}