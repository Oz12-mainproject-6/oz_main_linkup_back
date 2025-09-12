from tortoise import Tortoise
from app.config import TORTOISE_ORM


async def init_db():
    """데이터베이스 초기화"""
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()


async def close_db():
    """데이터베이스 연결 종료"""
    await Tortoise.close_connections()