"""Test utilities for FastAPI SDK."""

import pytest

from fastapi_sdk.utils.model import convert_model_name


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
