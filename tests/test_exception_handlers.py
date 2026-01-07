"""Tests for exception handlers."""

import pytest
from fastapi import FastAPI
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
