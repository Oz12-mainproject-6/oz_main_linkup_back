"""Tests for email verification functionality."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.features.users.models import EmailVerification, User
from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestEmailVerification:
    """Test email verification functionality."""

    @pytest.mark.asyncio
    async def test_send_verification_email_success(self, client, clean_users_db):
        """Test successful verification email sending."""
        with patch(
            "app.features.users.email_service.email_service.send_verification_email",
            new_callable=AsyncMock,
        ) as mock_send:
            mock_send.return_value = True

            response = client.post(
                "/api/auth/send-verification-email", json={"email": "test@example.com"}
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "인증 코드가 이메일로 전송되었습니다."
        assert data["email"] == "test@example.com"

        # 인증 코드가 생성되었는지 확인
        verification = await EmailVerification.filter(email="test@example.com").first()
        assert verification is not None
        assert len(verification.code) == 6
        assert verification.is_used is False

    @pytest.mark.asyncio
    async def test_send_verification_email_already_verified(
        self, client, clean_users_db
    ):
        """Test sending verification email to already verified user."""
        # 인증된 사용자 생성
        await User.create(
            email="verified@example.com",
            password="hashed_password",
            is_email_verified=True,
            user_type="fan",
        )

        response = client.post(
            "/api/auth/send-verification-email", json={"email": "verified@example.com"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "이미 인증된 이메일입니다" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_verify_email_success(self, client, clean_users_db):
        """Test successful email verification."""
        # 인증 코드 생성
        verification = await EmailVerification.create_verification_code(
            "test@example.com"
        )

        response = client.post(
            "/api/auth/verify-email",
            json={"email": "test@example.com", "code": verification.code},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "이메일 인증이 완료되었습니다."
        assert data["email"] == "test@example.com"

        # 인증 코드가 사용됨으로 표시되었는지 확인
        updated_verification = await EmailVerification.get(id=verification.id)
        assert updated_verification.is_used is True

    @pytest.mark.asyncio
    async def test_verify_email_with_existing_user(self, client, clean_users_db):
        """Test email verification with existing user."""
        # 미인증 사용자 생성
        user = await User.create(
            email="user@example.com",
            password="hashed_password",
            is_email_verified=False,
            user_type="fan",
        )

        # 인증 코드 생성
        verification = await EmailVerification.create_verification_code(
            "user@example.com"
        )

        response = client.post(
            "/api/auth/verify-email",
            json={"email": "user@example.com", "code": verification.code},
        )

        assert response.status_code == status.HTTP_200_OK

        # 사용자 인증 상태가 업데이트되었는지 확인
        updated_user = await User.get(id=user.id)
        assert updated_user.is_email_verified is True

    @pytest.mark.asyncio
    async def test_verify_email_invalid_code(self, client, clean_users_db):
        """Test email verification with invalid code."""
        response = client.post(
            "/api/auth/verify-email",
            json={
                "email": "test@example.com",
                "code": "123456",  # 존재하지 않는 코드
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "유효하지 않은 인증 코드입니다" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_verify_email_expired_code(self, client, clean_users_db):
        """Test email verification with expired code."""
        # 만료된 인증 코드 생성
        await EmailVerification.create(
            email="test@example.com",
            code="123456",
            expires_at=datetime.now(UTC) - timedelta(minutes=1),  # 1분 전 만료
            is_used=False,
        )

        response = client.post(
            "/api/auth/verify-email",
            json={"email": "test@example.com", "code": "123456"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "인증 코드가 만료되었습니다" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_verify_email_used_code(self, client, clean_users_db):
        """Test email verification with already used code."""
        # 사용된 인증 코드 생성
        await EmailVerification.create(
            email="test@example.com",
            code="123456",
            expires_at=datetime.now(UTC) + timedelta(minutes=10),
            is_used=True,  # 이미 사용됨
        )

        response = client.post(
            "/api/auth/verify-email",
            json={"email": "test@example.com", "code": "123456"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "유효하지 않은 인증 코드입니다" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_signup_with_verification_code_success(self, client, clean_users_db):
        """Test successful signup with email verification code."""
        # 인증 코드 생성
        verification = await EmailVerification.create_verification_code(
            "newuser@example.com"
        )

        response = client.post(
            "/api/auth/signup",
            json={
                "email": "newuser@example.com",
                "password": "password123",
                "nickname": "newuser",
                "user_type": "fan",
                "verification_code": verification.code,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["is_email_verified"] is True

        # 사용자가 생성되었는지 확인
        user = await User.filter(email="newuser@example.com").first()
        assert user is not None
        assert user.is_email_verified is True

        # 인증 코드가 사용됨으로 표시되었는지 확인
        updated_verification = await EmailVerification.get(id=verification.id)
        assert updated_verification.is_used is True

    @pytest.mark.asyncio
    async def test_signup_with_invalid_verification_code(self, client, clean_users_db):
        """Test signup with invalid verification code."""
        response = client.post(
            "/api/auth/signup",
            json={
                "email": "newuser@example.com",
                "password": "password123",
                "nickname": "newuser",
                "user_type": "fan",
                "verification_code": "999999",  # 존재하지 않는 6자리 코드
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "유효하지 않은 인증 코드입니다" in response.json()["detail"]

        # 사용자가 생성되지 않았는지 확인
        user = await User.filter(email="newuser@example.com").first()
        assert user is None

    @pytest.mark.asyncio
    async def test_signup_with_expired_verification_code(self, client, clean_users_db):
        """Test signup with expired verification code."""
        # 만료된 인증 코드 생성
        await EmailVerification.create(
            email="newuser@example.com",
            code="123456",
            expires_at=datetime.now(UTC) - timedelta(minutes=1),
            is_used=False,
        )

        response = client.post(
            "/api/auth/signup",
            json={
                "email": "newuser@example.com",
                "password": "password123",
                "nickname": "newuser",
                "user_type": "fan",
                "verification_code": "123456",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "인증 코드가 만료되었습니다" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_email_verification_code_generation(self, clean_users_db):
        """Test email verification code generation."""
        verification = await EmailVerification.create_verification_code(
            "test@example.com"
        )

        assert verification.email == "test@example.com"
        assert len(verification.code) == 6
        assert verification.code.isdigit()
        assert verification.is_used is False
        assert verification.expires_at > datetime.now(UTC)

    @pytest.mark.asyncio
    async def test_email_verification_code_replaces_existing(self, clean_users_db):
        """Test that new verification code replaces existing unused ones."""
        # 첫 번째 인증 코드 생성
        first_verification = await EmailVerification.create_verification_code(
            "test@example.com"
        )
        first_code = first_verification.code

        # 두 번째 인증 코드 생성 (같은 이메일)
        second_verification = await EmailVerification.create_verification_code(
            "test@example.com"
        )
        second_code = second_verification.code

        # 첫 번째 코드는 삭제되어야 함
        first_count = await EmailVerification.filter(code=first_code).count()
        assert first_count == 0

        # 두 번째 코드만 존재해야 함
        second_count = await EmailVerification.filter(code=second_code).count()
        assert second_count == 1
