import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.features.users.auth import get_password_hash
from app.features.users.models import User
from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestAuthSignup:
    """Test cases for user signup."""

    @pytest.mark.asyncio
    async def test_signup_success(self, client, clean_users_db):
        """Test successful user signup."""
        # 먼저 이메일 인증 코드 생성
        from app.features.users.models import EmailVerification

        verification = await EmailVerification.create_verification_code(
            "test@example.com"
        )

        response = client.post(
            "/api/auth/signup",
            json={
                "email": "test@example.com",
                "password": "password123",
                "nickname": "testuser",
                "user_type": "fan",
                "verification_code": verification.code,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["nickname"] == "testuser"
        assert data["user_type"] == "fan"
        assert data["is_email_verified"] is True
        assert "id" in data

    @pytest.mark.asyncio
    async def test_signup_duplicate_email(self, client, clean_users_db):
        """Test signup with duplicate email."""
        # Create a user first
        await User.create(
            email="test@example.com",
            password=get_password_hash("password123"),
            user_type="fan",
        )

        # 이메일 인증 코드 생성
        from app.features.users.models import EmailVerification

        verification = await EmailVerification.create_verification_code(
            "test@example.com"
        )

        response = client.post(
            "/api/auth/signup",
            json={
                "email": "test@example.com",
                "password": "password123",
                "nickname": "testuser2",
                "verification_code": verification.code,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "이미 등록된 이메일입니다" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_signup_company_user(self, client, clean_users_db):
        """Test company user signup."""
        # 이메일 인증 코드 생성
        from app.features.users.models import EmailVerification

        verification = await EmailVerification.create_verification_code(
            "company@example.com"
        )

        response = client.post(
            "/api/auth/signup",
            json={
                "email": "company@example.com",
                "password": "password123",
                "user_type": "company",
                "verification_code": verification.code,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_type"] == "company"
        assert data["is_email_verified"] is True


class TestAuthLogin:
    """Test cases for user login."""

    @pytest.mark.asyncio
    async def test_login_success(self, client, clean_users_db):
        """Test successful login."""
        # Create user first
        await User.create(
            email="test@example.com",
            password=get_password_hash("password123"),
            user_type="fan",
        )

        response = client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client, clean_users_db):
        """Test login with wrong password."""
        await User.create(
            email="test@example.com",
            password=get_password_hash("password123"),
            user_type="fan",
        )

        response = client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "wrongpassword"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client, clean_users_db):
        """Test login with non-existent user."""
        response = client.post(
            "/api/auth/login",
            json={"email": "nonexistent@example.com", "password": "password123"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuthLogout:
    """Test logout endpoint."""

    def test_logout(self, client):
        """Test logout endpoint."""
        response = client.post("/api/auth/logout")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "로그아웃되었습니다."
