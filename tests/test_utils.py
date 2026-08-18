"""Test utilities for FastAPI SDK."""

from datetime import UTC, datetime

from fastapi_sdk.utils.claims import claims_user_id, claims_user_name
from fastapi_sdk.utils.model import convert_model_name
from fastapi_sdk.utils.response import create_error_response, create_success_response
from fastapi_sdk.utils.schema import datetime_now_sec, serialize_datetime


def _parse(value: str) -> datetime:
    """Parse a serialized envelope timestamp back into a datetime."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


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


def test_success_response_timestamp_has_second_precision():
    """Envelope timestamps carry no microseconds, matching model fields.

    A response mixing `2026-01-01T00:00:00.123456Z` in meta with
    `2026-01-01T00:00:00Z` on the record it wraps is the same instant written
    two ways. `request_id` is what identifies a response; the timestamp does
    not need sub-second precision to do its job.
    """
    response = create_success_response(data={"ok": True})
    assert response["meta"]["timestamp"] == serialize_datetime(
        _parse(response["meta"]["timestamp"]).replace(microsecond=0)
    )
    assert "." not in response["meta"]["timestamp"]


def test_error_response_timestamp_has_second_precision():
    """Error envelopes use the same precision as success envelopes."""
    response = create_error_response(status_code=400, errors=["boom"])
    assert "." not in response["meta"]["timestamp"]


def test_envelope_and_model_timestamps_have_matching_shape():
    """The two timestamps in one response are written the same way."""
    envelope = create_success_response(data={"ok": True})["meta"]["timestamp"]
    model_field = serialize_datetime(datetime_now_sec())

    # Same length and format; only the instant may differ.
    assert len(envelope) == len(model_field)
    assert envelope.endswith("Z") and model_field.endswith("Z")


def test_claims_user_id_returns_sub():
    """The user id comes from the sub claim."""
    assert claims_user_id({"sub": "usr_abc"}) == "usr_abc"


def test_claims_user_id_without_claims():
    """Missing claims yield an empty string rather than raising."""
    assert claims_user_id(None) == ""
    assert claims_user_id({}) == ""


def test_claims_user_name_joins_first_and_last():
    """The display name is first and last joined."""
    claims = {"user_first_name": "Ada", "user_last_name": "Lovelace"}
    assert claims_user_name(claims) == "Ada Lovelace"


def test_claims_user_name_with_only_first_name():
    """A missing last name does not leave a trailing space."""
    assert claims_user_name({"user_first_name": "Ada"}) == "Ada"


def test_claims_user_name_with_only_last_name():
    """A missing first name does not leave a leading space."""
    assert claims_user_name({"user_last_name": "Lovelace"}) == "Lovelace"


def test_claims_user_name_falls_back_to_email():
    """With no name parts, the email identifies the user."""
    assert claims_user_name({"user_email": "ada@test.com"}) == "ada@test.com"


def test_claims_user_name_prefers_name_over_email():
    """The email is only a fallback, never preferred over a real name."""
    claims = {
        "user_first_name": "Ada",
        "user_last_name": "Lovelace",
        "user_email": "ada@test.com",
    }
    assert claims_user_name(claims) == "Ada Lovelace"


def test_claims_user_name_without_claims():
    """Missing claims yield an empty string rather than raising."""
    assert claims_user_name(None) == ""
    assert claims_user_name({}) == ""
