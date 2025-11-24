"""Tests for webhook utilities"""

import json
from unittest.mock import patch

import pytest
import requests
from requests.exceptions import RequestException, Timeout

from fastapi_sdk.webhook.generator import send_webhook


@pytest.fixture
def webhook_data():
    """Sample webhook data"""
    return {
        "url": "https://example.com/webhook",
        "secret": "test_secret",
        "event": "test.event",
        "data": {"id": 123, "name": "Test"},
        "meta_data": {"reference": "ref_123"},
    }


def test_send_webhook_success(webhook_data):
    """Test successful webhook delivery"""
    expected_response = {"status": "success"}

    with patch("requests.post") as mock_post:
        mock_response = mock_post.return_value
        mock_response.json.return_value = expected_response
        mock_response.raise_for_status.return_value = None

        result = send_webhook(**webhook_data)

        # Verify request was made correctly
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args

        assert args[0] == webhook_data["url"]
        assert kwargs["json"]["event"] == webhook_data["event"]
        assert kwargs["json"]["data"] == webhook_data["data"]
        assert kwargs["json"]["meta_data"] == webhook_data["meta_data"]
        assert "X-Signature" in kwargs["headers"]
        assert "X-Timestamp" in kwargs["headers"]
        assert kwargs["headers"]["Content-Type"] == "application/json"
        assert kwargs["timeout"] == 30

        # Verify response
        assert result == expected_response


def test_send_webhook_without_meta_data(webhook_data):
    """Test webhook delivery without meta_data"""
    webhook_data.pop("meta_data")
    expected_response = {"status": "success"}

    with patch("requests.post") as mock_post:
        mock_response = mock_post.return_value
        mock_response.json.return_value = expected_response
        mock_response.raise_for_status.return_value = None

        result = send_webhook(**webhook_data)

        # Verify meta_data is not in payload
        _, kwargs = mock_post.call_args
        assert "meta_data" not in kwargs["json"]

        assert result == expected_response


def test_send_webhook_timeout(webhook_data):
    """Test webhook timeout handling"""
    with patch("requests.post") as mock_post:
        mock_post.side_effect = Timeout("Request timed out")

        with pytest.raises(Timeout) as exc_info:
            send_webhook(**webhook_data)

        assert str(exc_info.value) == "Request timed out"


def test_send_webhook_request_error(webhook_data):
    """Test webhook request error handling"""
    with patch("requests.post") as mock_post:
        mock_post.side_effect = RequestException("Connection failed")

        with pytest.raises(RequestException) as exc_info:
            send_webhook(**webhook_data)

        assert str(exc_info.value) == "Connection failed"


def test_send_webhook_invalid_response(webhook_data):
    """Test webhook invalid response handling"""
    with patch("requests.post") as mock_post:
        mock_response = mock_post.return_value
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

        with pytest.raises(json.JSONDecodeError) as exc_info:
            send_webhook(**webhook_data)

        assert str(exc_info.value) == "Invalid JSON: line 1 column 1 (char 0)"


def test_send_webhook_non_200_response(webhook_data):
    """Test webhook non-200 response handling"""
    with patch("requests.post") as mock_post:
        mock_response = mock_post.return_value
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            "500 Server Error"
        )

        with pytest.raises(requests.HTTPError) as exc_info:
            send_webhook(**webhook_data)

        assert str(exc_info.value) == "500 Server Error"


def test_webhook_signature_format(webhook_data):
    """Test that generated signature is properly formatted"""
    with patch("requests.post") as mock_post:
        mock_response = mock_post.return_value
        mock_response.json.return_value = {"status": "success"}
        mock_response.raise_for_status.return_value = None

        send_webhook(**webhook_data)

        # Verify signature format
        _, kwargs = mock_post.call_args
        signature = kwargs["headers"]["X-Signature"]
        assert (
            len(signature) == 64
        ), f"Signature should be 64 characters, got {len(signature)}"
        assert all(
            c in "0123456789abcdef" for c in signature
        ), "Signature should contain only hexadecimal characters"


def test_webhook_timestamp_format(webhook_data):
    """Test that timestamp is properly formatted"""
    with patch("requests.post") as mock_post:
        mock_response = mock_post.return_value
        mock_response.json.return_value = {"status": "success"}
        mock_response.raise_for_status.return_value = None

        send_webhook(**webhook_data)

        # Verify timestamp format
        _, kwargs = mock_post.call_args
        timestamp = kwargs["headers"]["X-Timestamp"]
        assert timestamp.isdigit(), f"Timestamp should be numeric, got {timestamp}"
        assert int(timestamp) > 0, "Timestamp should be positive"


def test_send_webhook_success_logging(webhook_data, caplog):
    """Test successful webhook logging"""
    with patch("requests.post") as mock_post:
        mock_response = mock_post.return_value
        mock_response.json.return_value = {"status": "success"}
        mock_response.raise_for_status.return_value = None

        send_webhook(**webhook_data)

        # Verify logging messages
        log_messages = [record.message for record in caplog.records]
        assert any("Sending webhook to" in msg for msg in log_messages)
        assert any("Webhook sent successfully" in msg for msg in log_messages)


def test_send_webhook_edge_cases(webhook_data):
    """Test webhook with edge case data"""
    # Test with empty data
    empty_data = webhook_data.copy()
    empty_data["data"] = {}

    with patch("requests.post") as mock_post:
        mock_response = mock_post.return_value
        mock_response.json.return_value = {"status": "success"}
        mock_response.raise_for_status.return_value = None

        result = send_webhook(**empty_data)

        # Verify empty data is handled correctly
        _, kwargs = mock_post.call_args
        assert kwargs["json"]["data"] == {}
        assert result == {"status": "success"}

    # Test with explicit None meta_data
    none_meta_data = webhook_data.copy()
    none_meta_data["meta_data"] = None

    with patch("requests.post") as mock_post:
        mock_response = mock_post.return_value
        mock_response.json.return_value = {"status": "success"}
        mock_response.raise_for_status.return_value = None

        result = send_webhook(**none_meta_data)

        # Verify None meta_data is handled correctly (should not be in payload)
        _, kwargs = mock_post.call_args
        assert "meta_data" not in kwargs["json"]
        assert result == {"status": "success"}
