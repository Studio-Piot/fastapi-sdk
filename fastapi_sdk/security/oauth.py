"""Security utilities for handling JWT tokens and authentication.

This module provides functions for:
- Decoding and validating JWT access tokens
- Handling token expiration and signatures
"""

import json
import logging
from functools import lru_cache
from typing import Optional

import requests
from authlib.jose import JsonWebKey, JsonWebToken
from authlib.jose.errors import BadSignatureError, ExpiredTokenError, InvalidClaimError

from fastapi_sdk.utils.constants import ErrorCode

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

jwt = JsonWebToken(["RS256"])


class TokenError(Exception):
    """Base exception for token-related errors with error code."""

    def __init__(self, message: str, error_code: ErrorCode):
        """Initialize token error.

        Args:
            message: Human-readable error message
            error_code: Error code for the error
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class TokenExpiredError(TokenError):
    """Exception raised when a token has expired."""

    def __init__(self, message: str = "Token has expired"):
        """Initialize token expired error."""
        super().__init__(message, ErrorCode.TOKEN_EXPIRED)


class TokenInvalidSignatureError(TokenError):
    """Exception raised when a token has an invalid signature."""

    def __init__(self, message: str = "Invalid token signature"):
        """Initialize token invalid signature error."""
        super().__init__(message, ErrorCode.TOKEN_INVALID_SIGNATURE)


class TokenInvalidClaimError(TokenError):
    """Exception raised when a token has an invalid claim (e.g., wrong issuer)."""

    def __init__(self, message: str = "Invalid token claim"):
        """Initialize token invalid claim error."""
        super().__init__(message, ErrorCode.TOKEN_INVALID_CLAIM)


class TokenVerificationFailedError(TokenError):
    """Exception raised when token verification fails for other reasons."""

    def __init__(self, message: str = "Token verification failed"):
        """Initialize token verification failed error."""
        super().__init__(message, ErrorCode.TOKEN_VERIFICATION_FAILED)


@lru_cache()
def cached_jwk_response(jwk_url: str):
    """Cache JWK in memory"""
    return get_jwk(jwk_url)


def get_jwk(jwk_url: str):
    """
    Get the JWKS from the provided jwk_url.
    This is extracted as a single function to make it easier to mock in tests.

    Args:
        jwk_url: URL to fetch JWK from.
    """
    response = requests.get(
        jwk_url,
        timeout=10,
    )
    response.raise_for_status()
    jwk = response.json()
    return JsonWebKey.import_key(json.loads(jwk))


def decode_access_token(
    token: str,
    *,
    auth_issuer: str,
    auth_client_id: str,
    env: str,
    jwk_url: str,
    test_public_key_path: Optional[str] = None,
) -> dict:
    """Decode and validate a JWT token using the public key.

    Args:
        token: The JWT token to decode
        auth_issuer: The issuer of the JWT tokens
        auth_client_id: The client ID for authentication
        env: The environment (e.g., "test", "prod")
        jwk_url: URL to fetch JWK from. Required for all environments.
        test_public_key_path: Path to public key for test environment

    Returns:
        The decoded token claims

    Raises:
        TokenExpiredError: If the token has expired
        TokenInvalidSignatureError: If the token has an invalid signature
        TokenInvalidClaimError: If the token has an invalid claim (e.g., wrong issuer)
        TokenVerificationFailedError: If token verification fails for other reasons
    """
    try:
        # Configure claims validation options including issuer
        claims_options = {
            "iss": {"essential": True, "value": auth_issuer},
        }

        if env == "test" and test_public_key_path:
            with open(test_public_key_path, "rb") as f:
                test_public_key = f.read()
            claims = jwt.decode(token, test_public_key, claims_options=claims_options)
        else:
            # Get the JWKS from the issuer
            jwk = cached_jwk_response(jwk_url)
            claims = jwt.decode(token, jwk, claims_options=claims_options)

        # Validate expiration and other standard claims
        claims.validate()

        # Check if tenant_id matches auth_client_id
        if claims.get("tenant_id") != auth_client_id:
            logger.info("Token tenant_id does not match auth_client_id")
            raise TokenVerificationFailedError(
                "Token tenant_id does not match auth_client_id"
            )

        return claims
    except ExpiredTokenError as e:
        logger.info("Token has expired")
        raise TokenExpiredError("Token has expired") from e
    except BadSignatureError as e:
        logger.info("Invalid token signature")
        raise TokenInvalidSignatureError("Invalid token signature") from e
    except InvalidClaimError as e:
        logger.info("Invalid claim in token: %s", e)
        raise TokenInvalidClaimError(f"Invalid token claim: {str(e)}") from e
    except TokenError:
        # Re-raise token errors as-is
        raise
    except Exception as e:
        logger.info("Token verification failed: %s", e)
        raise TokenVerificationFailedError(
            f"Token verification failed: {str(e)}"
        ) from e
