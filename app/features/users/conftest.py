"""Shared fixtures for users feature tests."""

import pytest
from tortoise import Tortoise

from app.features.users.models import Company, User


@pytest.fixture(scope="session", autouse=True)
async def setup_users_test_db():
    """Setup test database for users feature."""
    await Tortoise.init(
        db_url="sqlite://:memory:", modules={"models": ["app.features.users.models"]}
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


@pytest.fixture
async def clean_users_db():
    """Clean users tables before each test."""
    await User.all().delete()
    await Company.all().delete()
    yield
