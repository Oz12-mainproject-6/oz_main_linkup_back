import asyncio
from collections.abc import AsyncGenerator

import pytest
from httpx import AsyncClient
from tortoise import Tortoise

from app.main import app

# 모든 모델의 경로를 포함하는 리스트
MODELS = [
    "aerich.models",
    "app.features.users.models",
    "app.features.artists.models",
    "app.features.events.models",
    "app.features.posts.models",
    "app.features.images.models",
    "app.features.notifications.models",
    "app.features.subscriptions.models",
]


@pytest.fixture(scope="session")
def event_loop():
    """pytest-asyncio의 기본 이벤트 루프 스코프를 세션으로 변경합니다."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def initialize_db(event_loop) -> AsyncGenerator[None, None]:
    """
    테스트 세션 시작 시 한 번만 테스트용 데이터베이스를 초기화합니다.
    """
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={"models": MODELS},
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


@pytest.fixture()
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    각 테스트 함수마다 독립적인 API 클라이언트를 제공합니다.
    """
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c
