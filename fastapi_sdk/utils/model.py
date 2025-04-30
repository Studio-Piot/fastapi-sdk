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


def convert_model_name(name: str) -> str:
    """Convert a model name from CamelCase to snake_case and remove 'model' suffix.

    Args:
        model_name: The model name to convert

    Returns:
        The converted model name in snake_case without 'model' suffix
    """
    # Remove the suffix 'Model' if it exists
    if name.endswith("Model"):
        name = name[:-5]

    # Convert CamelCase (preserving acronyms like API) to snake_case
    name = re.sub(
        r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name
    )  # Handle acronym followed by capital-lowercase
    name = re.sub(
        r"([a-z\d])([A-Z])", r"\1_\2", name
    )  # Handle lowercase/digit followed by uppercase
    return name.lower()
