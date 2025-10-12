import pytest
from tortoise import Tortoise

from app.features.artists.models import Artist, ArtistType
from app.features.notifications.models import Subscription
from app.features.users.models import Company, User, UserType


@pytest.fixture(scope="session", autouse=True)
async def setup_subscription_test_db():
    """Setup test database for subscription feature."""
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={
            "models": [
                "app.features.users.models",
                "app.features.artists.models",
                "app.features.notifications.models",
            ]
        },
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


@pytest.fixture
async def clean_subscription_db():
    """Clean subscription tables before each test."""
    await Subscription.all().delete()
    await Artist.all().delete()
    await Company.all().delete()
    await User.all().delete()
    yield


# -----------------------------
# 유저/아티스트 fixture
# -----------------------------
@pytest.fixture
async def fan_user():
    return await User.create(
        email="fan@test.com", password="test123", user_type=UserType.FAN
    )


@pytest.fixture
async def company_user():
    return await User.create(
        email="company@test.com", password="test123", user_type=UserType.COMPANY
    )


@pytest.fixture
async def company(company_user):
    return await Company.create(
        user=company_user,
        name="Test Company",
        business_number="123-45-67890",
        address="Test Address",
    )


@pytest.fixture
async def artist(company):
    return await Artist.create(
        company=company,
        stage_name="Test Artist",
        email="artist@test.com",
        artist_type=ArtistType.INDIVIDUAL,
    )


# -----------------------------
# 테스트: 구독 생성
# -----------------------------
@pytest.mark.asyncio
async def test_create_subscription(clean_subscription_db, fan_user, artist):
    sub = await Subscription.create(user=fan_user, artist=artist)
    assert sub.user.id == fan_user.id
    assert sub.artist.id == artist.id
    assert sub.is_active


# -----------------------------
# 테스트: 구독 목록 조회
# -----------------------------
@pytest.mark.asyncio
async def test_list_subscriptions(clean_subscription_db, fan_user, artist):
    # 미리 생성
    await Subscription.create(user=fan_user, artist=artist)

    subs = await Subscription.filter(user=fan_user, is_active=True).prefetch_related(
        "artist"
    )
    assert len(subs) == 1
    assert subs[0].artist.id == artist.id


# -----------------------------
# 테스트: 구독 취소
# -----------------------------
@pytest.mark.asyncio
async def test_cancel_subscription(clean_subscription_db, fan_user, artist):
    sub = await Subscription.create(user=fan_user, artist=artist)

    # 구독 취소
    sub.is_active = False
    await sub.save()

    sub_refreshed = await Subscription.get(id=sub.id)
    assert not sub_refreshed.is_active
