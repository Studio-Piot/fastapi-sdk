"""Schema utilities."""

from datetime import UTC, datetime
from typing import List

from pydantic import BaseModel, ConfigDict, TypeAdapter

_datetime_adapter = TypeAdapter(datetime)


def datetime_now_sec():
    """Return the current datetime with microseconds set to 0."""
    return datetime.now(UTC).replace(microsecond=0)


def serialize_datetime(dt: datetime) -> str:
    """Serialize a datetime for JSON API responses."""
    return _datetime_adapter.dump_python(dt, mode="json")


class BaseResponsePaginated(BaseModel):
    """Schema for paginatedAPI responses"""

    items: List[BaseModel]
    total: int
    page: int
    size: int
    pages: int

    model_config = ConfigDict(from_attributes=True)
