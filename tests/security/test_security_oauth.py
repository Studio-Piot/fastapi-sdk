"""Test security OAuth token decoding and exception handling."""

from datetime import timedelta

import pytest

from fastapi_sdk.security.oauth import (
    TokenExpiredError,
    TokenInvalidClaimError,
    TokenInvalidSignatureError,
    TokenVerificationFailedError,
    decode_access_token,
)
from fastapi_sdk.utils.constants import ErrorCode
from fastapi_sdk.utils.test import create_access_token
from tests.config import settings


def test_decode_access_token_success():
    """Test successful token decoding."""
    token = create_access_token(
        test_private_key_path=settings.TEST_PRIVATE_KEY_PATH,
        data={
            "sub": "test-user",
            "tenant_id": settings.AUTH_CLIENT_ID,
            "iss": settings.AUTH_ISSUER,
        },
    )

    claims = decode_access_token(
        token,
        auth_issuer=settings.AUTH_ISSUER,
        auth_client_id=settings.AUTH_CLIENT_ID,
        env=settings.ENVIRONMENT,
        jwk_url=settings.JWK_URL,
        test_public_key_path=settings.TEST_PUBLIC_KEY_PATH,
    )

    assert claims["sub"] == "test-user"
    assert claims["tenant_id"] == settings.AUTH_CLIENT_ID
    assert claims["iss"] == settings.AUTH_ISSUER


def test_decode_access_token_expired():
    """Test that decode_access_token raises TokenExpiredError for expired tokens."""
    expired_token = create_access_token(
        test_private_key_path=settings.TEST_PRIVATE_KEY_PATH,
        data={
            "sub": "test-user",
            "tenant_id": settings.AUTH_CLIENT_ID,
            "iss": settings.AUTH_ISSUER,
        },
        expires_delta=timedelta(minutes=-1),  # Expired token
    )

    with pytest.raises(TokenExpiredError) as exc_info:
        decode_access_token(
            expired_token,
            auth_issuer=settings.AUTH_ISSUER,
            auth_client_id=settings.AUTH_CLIENT_ID,
            env=settings.ENVIRONMENT,
            jwk_url=settings.JWK_URL,
            test_public_key_path=settings.TEST_PUBLIC_KEY_PATH,
        )

    assert exc_info.value.error_code == ErrorCode.TOKEN_EXPIRED
    assert "Token has expired" in exc_info.value.message


def test_decode_access_token_invalid_signature():
    """Test that decode_access_token raises TokenInvalidSignatureError for invalid signatures."""
    # Create a valid token first
    token = create_access_token(
        test_private_key_path=settings.TEST_PRIVATE_KEY_PATH,
        data={
            "sub": "test-user",
            "tenant_id": settings.AUTH_CLIENT_ID,
            "iss": settings.AUTH_ISSUER,
        },
    )

    # Corrupt the signature by modifying the last part of the token
    parts = token.split(".")
    corrupted_token = f"{parts[0]}.{parts[1]}.{parts[2][:-5]}XXXXX"

    with pytest.raises(TokenInvalidSignatureError) as exc_info:
        decode_access_token(
            corrupted_token,
            auth_issuer=settings.AUTH_ISSUER,
            auth_client_id=settings.AUTH_CLIENT_ID,
            env=settings.ENVIRONMENT,
            jwk_url=settings.JWK_URL,
            test_public_key_path=settings.TEST_PUBLIC_KEY_PATH,
        )

    assert exc_info.value.error_code == ErrorCode.TOKEN_INVALID_SIGNATURE
    assert "Invalid token signature" in exc_info.value.message


def test_decode_access_token_invalid_claim_wrong_issuer():
    """Test that decode_access_token raises TokenInvalidClaimError for wrong issuer."""
    token = create_access_token(
        test_private_key_path=settings.TEST_PRIVATE_KEY_PATH,
        data={
            "sub": "test-user",
            "tenant_id": settings.AUTH_CLIENT_ID,
            "iss": "https://wrong-issuer.com",  # Wrong issuer
        },
    )

    with pytest.raises(TokenInvalidClaimError) as exc_info:
        decode_access_token(
            token,
            auth_issuer=settings.AUTH_ISSUER,
            auth_client_id=settings.AUTH_CLIENT_ID,
            env=settings.ENVIRONMENT,
            jwk_url=settings.JWK_URL,
            test_public_key_path=settings.TEST_PUBLIC_KEY_PATH,
        )

    assert exc_info.value.error_code == ErrorCode.TOKEN_INVALID_CLAIM
    assert "Invalid token claim" in exc_info.value.message


def test_decode_access_token_verification_failed_wrong_tenant_id():
    """Test that decode_access_token raises TokenVerificationFailedError for wrong tenant_id."""
    token = create_access_token(
        test_private_key_path=settings.TEST_PRIVATE_KEY_PATH,
        data={
            "sub": "test-user",
            "tenant_id": "wrong-tenant-id",  # Wrong tenant_id
            "iss": settings.AUTH_ISSUER,
        },
    )

    with pytest.raises(TokenVerificationFailedError) as exc_info:
        decode_access_token(
            token,
            auth_issuer=settings.AUTH_ISSUER,
            auth_client_id=settings.AUTH_CLIENT_ID,
            env=settings.ENVIRONMENT,
            jwk_url=settings.JWK_URL,
            test_public_key_path=settings.TEST_PUBLIC_KEY_PATH,
        )

    assert exc_info.value.error_code == ErrorCode.TOKEN_VERIFICATION_FAILED
    assert "Token tenant_id does not match auth_client_id" in exc_info.value.message


def test_decode_access_token_malformed_token():
    """Test that decode_access_token raises TokenVerificationFailedError for malformed tokens."""
    malformed_token = "not.a.valid.jwt.token"

    with pytest.raises(TokenVerificationFailedError) as exc_info:
        decode_access_token(
            malformed_token,
            auth_issuer=settings.AUTH_ISSUER,
            auth_client_id=settings.AUTH_CLIENT_ID,
            env=settings.ENVIRONMENT,
            jwk_url=settings.JWK_URL,
            test_public_key_path=settings.TEST_PUBLIC_KEY_PATH,
        )

    assert exc_info.value.error_code == ErrorCode.TOKEN_VERIFICATION_FAILED
    assert "Token verification failed" in exc_info.value.message
