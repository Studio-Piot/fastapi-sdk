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
from authlib.jose.errors import BadSignatureError, ExpiredTokenError

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

jwt = JsonWebToken(["RS256"])


@lru_cache()
def cached_jwk_response(auth_issuer: str, auth_client_id: str):
    """Cache JWK in memory"""
    return get_jwk(auth_issuer, auth_client_id)


def get_jwk(auth_issuer: str, auth_client_id: str):
    """
    Get the JWKS from the JWKS_URL environment variable.
    This is extracted as a single function to make it easier to mock in tests.
    """
    response = requests.get(
        f"{auth_issuer}/auth/jwk?client_id={auth_client_id}",
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
    test_public_key_path: Optional[str] = None,
) -> dict:
    """Decode and validate a JWT token using the public key.

    Args:
        token: The JWT token to decode
        auth_issuer: The issuer of the JWT tokens
        auth_client_id: The client ID for authentication
        env: The environment (e.g., "test", "prod")
        test_public_key_path: Path to public key for test environment

    Returns:
        The decoded token claims

    Raises:
        ValueError: If the token is invalid, expired, or has an invalid signature
    """
    try:
        if env == "test" and test_public_key_path:
            with open(test_public_key_path, "rb") as f:
                test_public_key = f.read()
            claims = jwt.decode(token, test_public_key)
        else:
            # Get the JWKS from the issuer
            jwk = cached_jwk_response(auth_issuer, auth_client_id)
            claims = jwt.decode(token, jwk)

        # Validate expiration and other standard claims
        claims.validate()

        # Check if issuer matches auth_issuer
        if claims.get("iss") != auth_issuer:
            logger.info("Token issuer does not match auth_issuer")
            raise ValueError("Token issuer does not match auth_issuer")

        # Check if tenant_id matches auth_client_id
        if claims.get("tenant_id") != auth_client_id:
            logger.info("Token tenant_id does not match auth_client_id")
            raise ValueError("Token tenant_id does not match auth_client_id")

        return claims
    except ExpiredTokenError as e:
        logger.info("Token has expired")
        raise ValueError("Token has expired") from e
    except BadSignatureError as e:
        logger.info("Invalid token signature")
        raise ValueError("Invalid token signature") from e
    except Exception as e:
        logger.info("Token verification failed: %s", e)
        raise ValueError(f"Token verification failed: {str(e)}") from e
