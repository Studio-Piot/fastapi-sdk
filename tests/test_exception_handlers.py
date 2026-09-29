"""Tests for exception handlers."""

import pytest
from fastapi import FastAPI, Form
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from fastapi_sdk.utils.exception_handler import register_exception_handlers


class UserCreate(BaseModel):
    """User creation schema for testing."""

    name: str = Field(..., min_length=1)
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    age: int = Field(..., ge=0, le=150)


@pytest.fixture
def app():
    """Create a test FastAPI app with exception handlers."""
    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.post("/users/")
    async def create_user(user: UserCreate):
        return {"message": "User created", "user": user.model_dump()}

    @test_app.post("/users/manual/")
    async def create_user_manual(payload: dict):
        # Raise bare pydantic.ValidationError (not RequestValidationError)
        user = UserCreate.model_validate(payload)
        return {"message": "User created", "user": user.model_dump()}

    @test_app.post("/users/form/")
    async def create_user_form(
        name: str = Form(..., min_length=1),
        age: int = Form(...),
    ):
        return {"name": name, "age": age}

    @test_app.post("/users/form/manual/")
    async def create_user_form_manual(name: str = Form(""), age: str = Form("")):
        # Raise bare pydantic.ValidationError from form input
        user = UserCreate.model_validate({"name": name, "email": "", "age": age})
        return {"message": "User created", "user": user.model_dump()}

    return test_app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


def test_validation_error_includes_original_payload(client):
    """Test that validation errors include the original submitted payload."""
    # Send invalid data
    invalid_data = {
        "name": "",  # Too short
        "email": "not-an-email",  # Invalid format
        "age": "not-a-number",  # Invalid type
    }

    response = client.post("/users/", json=invalid_data)

    assert response.status_code == 422
    result = response.json()

    # Check response structure
    assert "status" in result
    assert result["status"]["code"] == 422
    assert result["status"]["message"] == "Unprocessable Entity"

    # Check that errors are present
    assert "errors" in result
    assert len(result["errors"]) > 0

    # Check that original data is included
    assert "data" in result
    assert result["data"] is not None
    assert result["data"]["name"] == ""
    assert result["data"]["email"] == "not-an-email"
    assert result["data"]["age"] == "not-a-number"

    # Check metadata
    assert "meta" in result
    assert "timestamp" in result["meta"]


def test_validation_error_with_missing_field(client):
    """Test validation error when required field is missing."""
    # Send incomplete data
    incomplete_data = {
        "name": "John Doe",
        "email": "john@example.com",
        # missing 'age' field
    }

    response = client.post("/users/", json=incomplete_data)

    assert response.status_code == 422
    result = response.json()
    print(result)

    # Check that errors are present
    assert "errors" in result
    errors = result["errors"]
    assert any(error["field"] == "age" for error in errors)
    assert any(error["code"] == "MISSING_REQUIRED" for error in errors)

    # Check that original data is included (even though it's incomplete)
    assert "data" in result
    assert result["data"] is not None
    assert result["data"]["name"] == "John Doe"
    assert result["data"]["email"] == "john@example.com"
    assert "age" not in result["data"]


def test_validation_error_with_multiple_errors(client):
    """Test validation error with multiple field errors."""
    invalid_data = {
        "name": "",  # Too short (min_length=1)
        "email": "invalid",  # Invalid format
        "age": 200,  # Out of range (max=150)
    }

    response = client.post("/users/", json=invalid_data)

    assert response.status_code == 422
    result = response.json()

    # Should have multiple errors
    assert "errors" in result
    assert len(result["errors"]) >= 3

    # Verify error codes
    error_fields = [error["field"] for error in result["errors"]]
    assert "name" in error_fields
    assert "email" in error_fields
    assert "age" in error_fields

    # Original data should still be present
    assert "data" in result
    assert result["data"]["name"] == ""
    assert result["data"]["email"] == "invalid"
    assert result["data"]["age"] == 200


def test_successful_request_has_null_errors(client):
    """Test that successful requests have null errors."""
    valid_data = {
        "name": "John Doe",
        "email": "john@example.com",
        "age": 30,
    }

    response = client.post("/users/", json=valid_data)

    assert response.status_code == 200
    result = response.json()

    # Successful response should not use the standard error format
    # It will return the endpoint's custom response
    assert "message" in result
    assert result["message"] == "User created"
    assert "user" in result
    assert result["user"]["name"] == "John Doe"


def test_validation_error_field_paths(client):
    """Test that field paths in errors are correctly formatted."""
    invalid_data = {
        "name": "Valid Name",
        "email": "invalid-email",
        "age": 25,
    }

    response = client.post("/users/", json=invalid_data)

    assert response.status_code == 422
    result = response.json()

    # Find the email error
    email_errors = [e for e in result["errors"] if e["field"] == "email"]
    assert len(email_errors) > 0

    # Verify error structure
    email_error = email_errors[0]
    assert "code" in email_error
    assert "message" in email_error
    assert email_error["code"] == "INVALID_FORMAT"


def test_pydantic_validation_error(client):
    """Test that bare pydantic.ValidationError is handled like RequestValidationError."""
    invalid_data = {
        "name": "",
        "email": "not-an-email",
        "age": "not-a-number",
    }

    response = client.post("/users/manual/", json=invalid_data)

    assert response.status_code == 422
    result = response.json()

    assert result["status"]["code"] == 422
    assert "errors" in result
    assert len(result["errors"]) > 0

    error_fields = [error["field"] for error in result["errors"]]
    assert "name" in error_fields
    assert "email" in error_fields
    assert "age" in error_fields

    # The submitted payload is read back from the request
    assert result["data"] == invalid_data


def test_form_validation_error_includes_original_payload(client):
    """Test that form validation errors return 422 with the submitted form data."""
    response = client.post("/users/form/", data={"name": "", "age": "not-a-number"})

    assert response.status_code == 422
    result = response.json()
    assert result["status"]["code"] == 422
    assert result["data"] == {"name": "", "age": "not-a-number"}
    assert {error["field"] for error in result["errors"]} == {"name", "age"}


def test_pydantic_validation_error_with_form_payload(client):
    """Test that bare pydantic.ValidationError returns submitted form data."""
    response = client.post(
        "/users/form/manual/", data={"name": "", "age": "not-a-number"}
    )

    assert response.status_code == 422
    result = response.json()
    assert result["data"] == {"name": "", "age": "not-a-number"}


def _debug_app(debug: bool) -> FastAPI:
    test_app = FastAPI()
    register_exception_handlers(test_app, debug=debug)

    @test_app.post("/users/")
    async def create_user(user: UserCreate):
        return user.model_dump()

    return test_app


def test_debug_mode_logs_error_responses(caplog):
    """Test that debug mode logs the method, path, status and response body."""
    client = TestClient(_debug_app(debug=True))

    with caplog.at_level("WARNING", logger="fastapi_sdk.errors"):
        client.post("/users/", json={"name": "", "email": "x", "age": 1})

    records = [r for r in caplog.records if r.name == "fastapi_sdk.errors"]
    assert len(records) == 1
    message = records[0].getMessage()
    assert "POST /users/ -> 422" in message
    assert '"email": "x"' in message


def test_error_responses_not_logged_by_default(caplog):
    """Test that error responses are not logged unless debug mode is on."""
    client = TestClient(_debug_app(debug=False))

    with caplog.at_level("DEBUG", logger="fastapi_sdk.errors"):
        client.post("/users/", json={"name": "", "email": "x", "age": 1})

    assert not [r for r in caplog.records if r.name == "fastapi_sdk.errors"]



class SignupCreate(BaseModel):
    """Signup schema with sensitive fields for masking tests."""

    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    password: str = Field(..., min_length=8)
    billing: dict


def _signup_app(**kwargs) -> FastAPI:
    test_app = FastAPI()
    register_exception_handlers(test_app, **kwargs)

    @test_app.post("/signup/")
    async def signup(data: SignupCreate):
        return data.model_dump()

    return test_app


SIGNUP_PAYLOAD = {
    "email": "not-an-email",
    "password": "hunter2",
    "billing": {"card_number": "4242424242424242", "Client-Secret": "s3", "city": "X"},
}


def _signup_log(caplog, **kwargs) -> tuple[dict, str]:
    client = TestClient(_signup_app(debug=True, **kwargs))
    with caplog.at_level("WARNING", logger="fastapi_sdk.errors"):
        response = client.post("/signup/", json=SIGNUP_PAYLOAD)
    records = [r for r in caplog.records if r.name == "fastapi_sdk.errors"]
    return response.json(), records[0].getMessage()


def test_debug_log_masks_sensitive_fields_but_response_does_not(caplog):
    """Test that sensitive values are masked in the log but echoed in the response."""
    result, message = _signup_log(caplog)

    assert result["data"] == SIGNUP_PAYLOAD
    assert '"password": "***"' in message
    assert '"card_number": "***"' in message
    assert '"Client-Secret": "***"' in message
    assert '"city": "X"' in message
    for secret in ("hunter2", "4242424242424242", "s3"):
        assert secret not in message


def test_debug_log_masks_custom_sensitive_fields(caplog):
    """Test that a custom sensitive_fields list replaces the defaults."""
    _, message = _signup_log(caplog, sensitive_fields={"email"})

    assert '"email": "***"' in message
    assert '"password": "hunter2"' in message
