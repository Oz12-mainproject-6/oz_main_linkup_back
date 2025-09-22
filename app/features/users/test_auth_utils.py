from datetime import datetime, timedelta

from app.features.users.auth import (
    create_access_token,
    get_password_hash,
    verify_password,
    verify_token,
)


class TestPasswordHashing:
    """Test password hashing functionality."""

    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "test_password_123"
        hashed = get_password_hash(password)

        # Hash should be different from original
        assert hashed != password
        assert len(hashed) > 20  # bcrypt hashes are long
        assert hashed.startswith("$2b$")  # bcrypt format

    def test_password_verification_success(self):
        """Test successful password verification."""
        password = "my_secure_password"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_password_verification_failure(self):
        """Test failed password verification."""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False

    def test_different_passwords_different_hashes(self):
        """Test that same password generates different hashes (salt)."""
        password = "same_password"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Should be different due to salt
        assert hash1 != hash2
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokens:
    """Test JWT token functionality."""

    def test_create_access_token(self):
        """Test JWT token creation."""
        data = {"sub": "123", "email": "test@example.com"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 20
        # JWT tokens have 3 parts separated by dots
        assert len(token.split(".")) == 3

    def test_verify_valid_token(self):
        """Test verification of valid token."""
        data = {"sub": "123", "email": "test@example.com"}
        token = create_access_token(data)

        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "123"
        assert payload["email"] == "test@example.com"
        assert "exp" in payload  # Should have expiration

    def test_verify_invalid_token(self):
        """Test verification of invalid token."""
        invalid_token = "invalid.jwt.token"
        payload = verify_token(invalid_token)
        assert payload is None

    def test_token_with_custom_expiration(self):
        """Test token creation with custom expiration."""
        data = {"sub": "123"}
        custom_expiry = timedelta(minutes=30)
        token = create_access_token(data, expires_delta=custom_expiry)

        payload = verify_token(token)
        assert payload is not None

        # Check that expiration is set
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp)
        now = datetime.now()

        # Should expire in approximately 30 minutes
        time_diff = exp_datetime - now
        assert 25 <= time_diff.total_seconds() / 60 <= 35  # Allow some margin

    def test_token_contains_required_fields(self):
        """Test that token contains all required fields."""
        data = {"sub": "user_123", "email": "user@example.com", "user_type": "fan"}
        token = create_access_token(data)
        payload = verify_token(token)

        assert payload["sub"] == "user_123"
        assert payload["email"] == "user@example.com"
        assert payload["user_type"] == "fan"
        assert "exp" in payload
