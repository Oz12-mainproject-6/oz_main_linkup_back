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
            },
        }
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
            ],
            "default_connection": "default",
        }
    },
}
