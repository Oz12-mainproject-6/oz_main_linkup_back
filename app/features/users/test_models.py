import pytest
from tortoise.exceptions import IntegrityError

from app.features.users.models import Company, User, UserType


class TestUserModel:
    """Test User model functionality."""

    @pytest.mark.asyncio
    async def test_create_user(self, clean_users_db):
        """Test user creation."""
        user = await User.create(
            email="test@example.com",
            password="hashed_password",
            nickname="testuser",
            user_type=UserType.FAN,
        )

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.nickname == "testuser"
        assert user.user_type == UserType.FAN
        assert user.push_notification_enabled is True  # default
        assert user.in_app_notification_enabled is True  # default

    @pytest.mark.asyncio
    async def test_user_type_enum(self, clean_users_db):
        """Test UserType enum functionality."""
        fan_user = await User.create(
            email="fan@example.com", password="password", user_type=UserType.FAN
        )

        company_user = await User.create(
            email="company@example.com", password="password", user_type=UserType.COMPANY
        )

        assert fan_user.user_type == UserType.FAN
        assert company_user.user_type == UserType.COMPANY

        # Test enum values
        assert UserType.FAN.value == "fan"
        assert UserType.COMPANY.value == "company"

    @pytest.mark.asyncio
    async def test_unique_email_constraint(self, clean_users_db):
        """Test that email must be unique."""
        await User.create(
            email="test@example.com", password="password1", user_type=UserType.FAN
        )

        # This should raise an exception due to unique constraint
        with pytest.raises(IntegrityError):
            await User.create(
                email="test@example.com",
                password="password2",
                user_type=UserType.COMPANY,
            )

    @pytest.mark.asyncio
    async def test_user_defaults(self, clean_users_db):
        """Test default values for user fields."""
        user = await User.create(email="test@example.com", password="password")

        assert user.user_type == UserType.FAN  # default
        assert user.push_notification_enabled is True
        assert user.in_app_notification_enabled is True
        assert user.phone_number is None
        assert user.nickname is None
        assert user.oauth_provider is None
        assert user.oauth_id is None


class TestCompanyModel:
    """Test Company model functionality."""

    @pytest.mark.asyncio
    async def test_create_company(self, clean_users_db):
        """Test company creation with user relationship."""
        # Create company user first
        user = await User.create(
            email="company@example.com", password="password", user_type=UserType.COMPANY
        )

        company = await Company.create(
            user=user,
            name="Test Company",
            business_number="123-45-67890",
            contact_email="contact@company.com",
        )

        assert company.id is not None
        assert company.name == "Test Company"
        assert company.business_number == "123-45-67890"
        assert company.contact_email == "contact@company.com"
        assert company.user_id == user.id

    @pytest.mark.asyncio
    async def test_company_user_relationship(self, clean_users_db):
        """Test OneToOne relationship between Company and User."""
        user = await User.create(
            email="company@example.com", password="password", user_type=UserType.COMPANY
        )

        company = await Company.create(user=user, name="Test Company")

        # Test forward relationship
        assert company.user_id == user.id

        # Test reverse relationship
        user_with_company = await User.get(id=user.id).prefetch_related(
            "company_profile"
        )
        assert user_with_company.company_profile.name == "Test Company"
