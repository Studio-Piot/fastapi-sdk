"""Utility functions for testing"""

from datetime import timedelta
from typing import Optional

from joserfc import jwt
from joserfc.jwk import RSAKey

from fastapi_sdk.utils.schema import datetime_now_sec

ALGORITHM = "RS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(
    test_private_key_path: str, data: dict, expires_delta: Optional[timedelta] = None
) -> str:
    """Generate an asymmetric JWT token signed with a private key."""
    expire = datetime_now_sec() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {**data, "exp": expire}
    with open(test_private_key_path, "rb") as f:
        private_key = RSAKey.import_key(f.read())
    return jwt.encode({"alg": ALGORITHM}, payload, private_key)
