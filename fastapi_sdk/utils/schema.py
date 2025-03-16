"""Schema utilities."""

from datetime import UTC, datetime


def datetime_now_sec():
    """Return the current datetime with microseconds set to 0."""
    return datetime.now(UTC).replace(microsecond=0)
