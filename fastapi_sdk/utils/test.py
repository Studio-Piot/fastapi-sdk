"""Utility functions for testing"""

from datetime import UTC, datetime, timedelta
from typing import Optional

from authlib.jose import JsonWebToken

ALGORITHM = "RS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

jwt = JsonWebToken(["RS256"])


def create_access_token(
    test_private_key_path: str, data: dict, expires_delta: Optional[timedelta] = None
) -> str:
    """Generate an asymmetric JWT token signed with a private key."""
    expire = datetime.now(UTC).replace(microsecond=0) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {**data, "exp": expire}
    with open(test_private_key_path, "rb") as f:
        test_private_key = f.read()
    token = jwt.encode({"alg": ALGORITHM}, payload, test_private_key)
    return token.decode("utf-8")
