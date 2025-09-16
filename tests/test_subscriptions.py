import pytest
from tortoise.contrib.test import initializer, finalizer
from app.features.users.models import User, UserType
from app.features.subscriptions.models import Subscription, Artist
from app.features.subscriptions.router import subscriptions_router
from fastapi.testclient import TestClient
from app.main import app


# -----------------------------
# DB 초기화/종료 fixture
# -----------------------------
@pytest.fixture(scope="module", autouse=True)
def init_db():
    initializer(
        modules={
            "models": [
                "app.features.users.models",
                "app.features.subscriptions.models"
            ]
        },
        db_url="sqlite://:memory:"
    )
    yield
    finalizer()


# -----------------------------
# FastAPI TestClient
# -----------------------------
@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# -----------------------------
# 유저/아티스트 fixture
# -----------------------------
@pytest.fixture
async def fan_user():
    return await User.create(
        email="fan@test.com",
        password="test123",
        user_type=UserType.FAN
    )


@pytest.fixture
async def artist_user():
    return await User.create(
        email="artist@test.com",
        password="test123",
        user_type=UserType.COMPANY
    )


@pytest.fixture
async def artist(artist_user):
    return await Artist.create(
        user=artist_user,
        name="Test Artist"
    )


# -----------------------------
# 테스트: 구독 생성
# -----------------------------
@pytest.mark.anyio
async def test_create_subscription(fan_user, artist):
    sub = await Subscription.create(user=fan_user, artist=artist)
    assert sub.user.id == fan_user.id
    assert sub.artist.id == artist.id
    assert sub.is_active


# -----------------------------
# 테스트: 구독 목록 조회
# -----------------------------
@pytest.mark.anyio
async def test_list_subscriptions(fan_user, artist):
    # 미리 생성
    await Subscription.create(user=fan_user, artist=artist)

    subs = await Subscription.filter(user=fan_user, is_active=True)
    assert len(subs) == 1
    assert subs[0].artist.id == artist.id


# -----------------------------
# 테스트: 구독 취소
# -----------------------------
@pytest.mark.anyio
async def test_cancel_subscription(fan_user, artist):
    sub = await Subscription.create(user=fan_user, artist=artist)

    # 구독 취소
    sub.is_active = False
    await sub.save()

    sub_refreshed = await Subscription.get(id=sub.id)
    assert not sub_refreshed.is_active
