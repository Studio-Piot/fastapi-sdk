"""Set of utilities to create and manage models."""

import re
from typing import Annotated

import shortuuid
from pydantic import StringConstraints


class ShortUUID:
    """Custom type for short UUIDs with trigram prefixes"""

    @classmethod
    def generate(cls, prefix: str) -> str:
        """Generate a valid short UUID with a given trigram prefix"""
        if not re.match(r"^[a-z]{3}$", prefix):
            raise ValueError("Prefix must be exactly 3 lowercase letters")
        return f"{prefix}_{shortuuid.uuid()[:10]}"

    @classmethod
    def validate(cls, value: str) -> str:
        """Validate the short UUID format"""
        if not re.match(r"^[a-z]{3}_[a-zA-Z0-9]{10}$", value):
            raise ValueError("Invalid short UUID format")
        return value


ShortUUIDType = Annotated[str, StringConstraints(pattern=r"^[a-z]{3}_[a-zA-Z0-9]{10}$")]
