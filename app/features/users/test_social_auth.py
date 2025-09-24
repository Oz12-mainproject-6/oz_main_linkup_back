"""Tests for social authentication functionality."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.features.users.models import User
from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestSocialLogin:
    """Test social login functionality."""

    @pytest.mark.asyncio
    async def test_google_social_login_new_user(self, client, clean_users_db):
        """Test Google social login with new user."""
        mock_user_info = {
            "provider": "google",
            "oauth_id": "google_123456",
            "email": "test@gmail.com",
            "name": "Test User",
            "picture": "https://example.com/picture.jpg",
        }

        with patch(
            "app.features.users.service.get_oauth_user_info", new_callable=AsyncMock
        ) as mock_oauth:
            mock_oauth.return_value = mock_user_info

            response = client.post(
                "/api/auth/social-login",
                json={
                    "provider": "google",
                    "access_token": "mock_google_token",
                    "user_type": "fan",
                },
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

        # 사용자가 생성되었는지 확인
        user = await User.filter(email="test@gmail.com").first()
        assert user is not None
        assert user.oauth_provider == "google"
        assert user.oauth_id == "google_123456"
        assert user.nickname == "Test User"

    @pytest.mark.asyncio
    async def test_kakao_social_login_new_user(self, client, clean_users_db):
        """Test Kakao social login with new user."""
        mock_user_info = {
            "provider": "kakao",
            "oauth_id": "kakao_789012",
            "email": "test@kakao.com",
            "name": "카카오 사용자",
            "picture": "https://example.com/kakao_picture.jpg",
        }

        with patch(
            "app.features.users.service.get_oauth_user_info", new_callable=AsyncMock
        ) as mock_oauth:
            mock_oauth.return_value = mock_user_info

            response = client.post(
                "/api/auth/social-login",
                json={
                    "provider": "kakao",
                    "access_token": "mock_kakao_token",
                    "user_type": "fan",
                },
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data

        # 사용자가 생성되었는지 확인
        user = await User.filter(email="test@kakao.com").first()
        assert user is not None
        assert user.oauth_provider == "kakao"
        assert user.oauth_id == "kakao_789012"

    @pytest.mark.asyncio
    async def test_social_login_existing_user(self, client, clean_users_db):
        """Test social login with existing user."""
        # 기존 사용자 생성
        existing_user = await User.create(
            email="existing@gmail.com",
            password="hashed_password",
            oauth_provider="google",
            oauth_id="google_existing",
            user_type="fan",
        )

        mock_user_info = {
            "provider": "google",
            "oauth_id": "google_existing",
            "email": "existing@gmail.com",
            "name": "Existing User",
        }

        with patch(
            "app.features.users.service.get_oauth_user_info", new_callable=AsyncMock
        ) as mock_oauth:
            mock_oauth.return_value = mock_user_info

            response = client.post(
                "/api/auth/social-login",
                json={
                    "provider": "google",
                    "access_token": "mock_google_token",
                    "user_type": "fan",
                },
            )

        assert response.status_code == status.HTTP_200_OK

        # 새로운 사용자가 생성되지 않았는지 확인
        users_count = await User.filter(email="existing@gmail.com").count()
        assert users_count == 1

        # 마지막 로그인 시간이 업데이트되었는지 확인
        updated_user = await User.get(id=existing_user.id)
        assert updated_user.last_login_at is not None

    @pytest.mark.asyncio
    async def test_social_login_link_existing_email(self, client, clean_users_db):
        """Test social login linking to existing email account."""
        # 일반 계정으로 기존 사용자 생성 (소셜 정보 없음)
        existing_user = await User.create(
            email="linkuser@gmail.com",
            password="hashed_password",
            user_type="fan",
        )

        mock_user_info = {
            "provider": "google",
            "oauth_id": "google_newlink",
            "email": "linkuser@gmail.com",
            "name": "Link User",
        }

        with patch(
            "app.features.users.service.get_oauth_user_info", new_callable=AsyncMock
        ) as mock_oauth:
            mock_oauth.return_value = mock_user_info

            response = client.post(
                "/api/auth/social-login",
                json={
                    "provider": "google",
                    "access_token": "mock_google_token",
                    "user_type": "fan",
                },
            )

        assert response.status_code == status.HTTP_200_OK

        # 기존 계정에 소셜 정보가 연동되었는지 확인
        updated_user = await User.get(id=existing_user.id)
        assert updated_user.oauth_provider == "google"
        assert updated_user.oauth_id == "google_newlink"

        # 새로운 사용자가 생성되지 않았는지 확인
        users_count = await User.filter(email="linkuser@gmail.com").count()
        assert users_count == 1

    @pytest.mark.asyncio
    async def test_social_login_invalid_token(self, client, clean_users_db):
        """Test social login with invalid token."""
        with patch(
            "app.features.users.service.get_oauth_user_info", new_callable=AsyncMock
        ) as mock_oauth:
            mock_oauth.return_value = None  # 토큰 검증 실패

            response = client.post(
                "/api/auth/social-login",
                json={
                    "provider": "google",
                    "access_token": "invalid_token",
                    "user_type": "fan",
                },
            )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "소셜 로그인 토큰이 유효하지 않습니다" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_social_login_no_email(self, client, clean_users_db):
        """Test social login when no email is provided - should create temp email."""
        mock_user_info = {
            "provider": "google",
            "oauth_id": "google_no_email",
            "email": None,  # 이메일 없음
            "name": "No Email User",
        }

        with patch(
            "app.features.users.service.get_oauth_user_info", new_callable=AsyncMock
        ) as mock_oauth:
            mock_oauth.return_value = mock_user_info

            response = client.post(
                "/api/auth/social-login",
                json={
                    "provider": "google",
                    "access_token": "mock_google_token",
                    "user_type": "fan",
                },
            )

        # 이메일이 없어도 임시 이메일로 성공해야 함
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data

        # 생성된 사용자 확인
        user = await User.filter(
            oauth_provider="google", oauth_id="google_no_email"
        ).first()
        assert user is not None
        assert user.email == "google_google_no_email@temp.linkup.com"
        assert user.is_email_verified is False

    @pytest.mark.asyncio
    async def test_social_login_unsupported_provider(self, client, clean_users_db):
        """Test social login with unsupported provider."""
        response = client.post(
            "/api/auth/social-login",
            json={
                "provider": "facebook",  # 지원하지 않는 제공자
                "access_token": "mock_token",
                "user_type": "fan",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "지원하지 않는 OAuth 제공자입니다" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_social_login_company_user(self, client, clean_users_db):
        """Test social login for company user type."""
        mock_user_info = {
            "provider": "google",
            "oauth_id": "google_company",
            "email": "company@gmail.com",
            "name": "Company User",
        }

        with patch(
            "app.features.users.service.get_oauth_user_info", new_callable=AsyncMock
        ) as mock_oauth:
            mock_oauth.return_value = mock_user_info

            response = client.post(
                "/api/auth/social-login",
                json={
                    "provider": "google",
                    "access_token": "mock_google_token",
                    "user_type": "company",
                },
            )

        assert response.status_code == status.HTTP_200_OK

        # 소속사 타입으로 사용자가 생성되었는지 확인
        user = await User.filter(email="company@gmail.com").first()
        assert user is not None
        assert user.user_type.value == "company"
