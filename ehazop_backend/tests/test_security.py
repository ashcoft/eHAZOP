"""Tests for security module."""

from datetime import timedelta

import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_access_token,
    verify_refresh_token,
)


class TestAccessToken:
    """Tests for access token functions."""

    def test_create_access_token_basic(self):
        """Basic access token creation."""
        data = {"sub": "user123", "role": "admin"}
        token = create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_custom_expiry(self):
        """Access token with custom expiry time."""
        data = {"sub": "user123"}
        expires = timedelta(minutes=60)
        token = create_access_token(data, expires_delta=expires)
        assert isinstance(token, str)

    def test_decode_access_token(self):
        """Access token should be decodable."""
        data = {"sub": "user123", "role": "admin"}
        token = create_access_token(data)
        decoded = decode_token(token)
        assert decoded["sub"] == "user123"
        assert decoded["role"] == "admin"
        assert decoded["type"] == "access"
        assert "exp" in decoded

    def test_verify_access_token_valid(self):
        """Valid access token should verify successfully."""
        data = {"sub": "user123"}
        token = create_access_token(data)
        payload = verify_access_token(token)
        assert payload["sub"] == "user123"
        assert payload["type"] == "access"

    def test_verify_access_token_invalid_type(self):
        """Refresh token should fail access token verification."""
        data = {"sub": "user123"}
        token = create_refresh_token(data)
        with pytest.raises(ValueError, match="Invalid token type"):
            verify_access_token(token)

    def test_decode_invalid_token(self):
        """Invalid token should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid token"):
            decode_token("invalid.token.here")

    def test_decode_empty_token(self):
        """Empty token should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid token"):
            decode_token("")


class TestRefreshToken:
    """Tests for refresh token functions."""

    def test_create_refresh_token_basic(self):
        """Basic refresh token creation."""
        data = {"sub": "user123"}
        token = create_refresh_token(data)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token_with_custom_expiry(self):
        """Refresh token with custom expiry time."""
        data = {"sub": "user123"}
        expires = timedelta(days=14)
        token = create_refresh_token(data, expires_delta=expires)
        assert isinstance(token, str)

    def test_decode_refresh_token(self):
        """Refresh token should be decodable."""
        data = {"sub": "user123"}
        token = create_refresh_token(data)
        decoded = decode_token(token)
        assert decoded["sub"] == "user123"
        assert decoded["type"] == "refresh"
        assert "exp" in decoded

    def test_verify_refresh_token_valid(self):
        """Valid refresh token should verify successfully."""
        data = {"sub": "user123"}
        token = create_refresh_token(data)
        payload = verify_refresh_token(token)
        assert payload["sub"] == "user123"
        assert payload["type"] == "refresh"

    def test_verify_refresh_token_invalid_type(self):
        """Access token should fail refresh token verification."""
        data = {"sub": "user123"}
        token = create_access_token(data)
        with pytest.raises(ValueError, match="Invalid token type"):
            verify_refresh_token(token)


class TestTokenExpiry:
    """Tests for token expiry functionality."""

    def test_access_token_expiry_default(self):
        """Access token should have default expiry."""
        data = {"sub": "user123"}
        token = create_access_token(data)
        decoded = decode_token(token)
        assert "exp" in decoded

    def test_access_token_expiry_custom(self):
        """Access token with custom expiry should have correct exp."""
        data = {"sub": "user123"}
        expires = timedelta(hours=1)
        token = create_access_token(data, expires_delta=expires)
        decoded = decode_token(token)
        assert "exp" in decoded


class TestTokenDataIntegrity:
    """Tests for token data handling."""

    def test_token_data_not_modified(self):
        """Original data should not be modified."""
        original_data = {"sub": "user123", "role": "admin"}
        data_copy = original_data.copy()
        create_access_token(original_data)
        assert original_data == data_copy

    def test_token_with_special_characters(self):
        """Token with special characters in data should work."""
        data = {"sub": "user@example.com", "name": "John Doe"}
        token = create_access_token(data)
        decoded = decode_token(token)
        assert decoded["sub"] == "user@example.com"
        assert decoded["name"] == "John Doe"

    def test_token_with_unicode_data(self):
        """Token with unicode data should work."""
        data = {"sub": "user123", "name": "日本語テスト"}
        token = create_access_token(data)
        decoded = decode_token(token)
        assert decoded["name"] == "日本語テスト"