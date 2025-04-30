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


def convert_model_name(model_name: str) -> str:
    """Convert a model name from CamelCase to snake_case and remove 'model' suffix.

    Args:
        model_name: The model name to convert

    Returns:
        The converted model name in snake_case without 'model' suffix
    """
    # Convert to lowercase and remove model suffix
    name = model_name.lower().replace("model", "")
    # Convert CamelCase to snake_case
    name = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
    # Remove any remaining "model" word
    return name.replace("_model", "")
