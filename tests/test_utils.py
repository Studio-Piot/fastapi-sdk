"""Test utilities for FastAPI SDK."""

from datetime import UTC, datetime

from fastapi_sdk.utils.model import convert_model_name
from fastapi_sdk.utils.response import create_success_response
from fastapi_sdk.utils.schema import serialize_datetime


def test_convert_model_name_basic():
    """Test basic model name conversion."""
    assert convert_model_name("UserModel") == "user"
    assert convert_model_name("ProjectModel") == "project"
    assert convert_model_name("TaskModel") == "task"


def test_convert_model_name_camel_case():
    """Test conversion of CamelCase model names."""
    assert convert_model_name("UserProfileModel") == "user_profile"
    assert convert_model_name("ProjectTaskModel") == "project_task"
    assert convert_model_name("AccountSettingsModel") == "account_settings"


def test_convert_model_name_no_model_suffix():
    """Test conversion of model names without 'Model' suffix."""
    assert convert_model_name("User") == "user"
    assert convert_model_name("Project") == "project"
    assert convert_model_name("UserProfile") == "user_profile"


def test_convert_model_name_special_cases():
    """Test special cases for model name conversion."""
    assert convert_model_name("APIUserModel") == "api_user"
    assert convert_model_name("HTTPRequestModel") == "http_request"
    assert convert_model_name("JSONDataModel") == "json_data"


def test_serialize_datetime_uses_z_suffix_for_utc():
    """UTC datetimes should serialize with a Z suffix, matching Pydantic JSON mode."""
    dt = datetime(2026, 6, 5, 13, 50, 13, tzinfo=UTC)
    assert serialize_datetime(dt) == "2026-06-05T13:50:13Z"


def test_create_success_response_timestamp_uses_z_suffix():
    """Response metadata timestamps should use the same UTC format as model fields."""
    response = create_success_response(data={"ok": True})
    assert response["meta"]["timestamp"].endswith("Z")
