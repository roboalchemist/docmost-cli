"""Tests for DocmostClient and HTTP error handling."""

from unittest.mock import patch

import httpx
import pytest

from docmost.client import (
    AuthenticationError,
    DocmostClient,
    DocmostError,
    NotFoundError,
    ValidationError,
    get_client,
)


class TestDocmostClientInit:
    """Tests for DocmostClient initialization."""

    def test_init_with_explicit_url_and_token(self) -> None:
        """Client accepts explicit URL and token."""
        client = DocmostClient(url="https://docs.example.com/api", token="test-token")
        assert client.url == "https://docs.example.com/api"
        assert client.token == "test-token"
        assert client.timeout == 30.0

    def test_init_with_custom_timeout(self) -> None:
        """Client accepts custom timeout."""
        client = DocmostClient(
            url="https://docs.example.com/api", token="test-token", timeout=60.0
        )
        assert client.timeout == 60.0

    def test_init_without_url_raises_error(self) -> None:
        """Client raises error when no URL is configured."""
        with patch("docmost.client.get_url", return_value=None):
            with patch("docmost.client.get_token", return_value="token"):
                with pytest.raises(DocmostError) as exc_info:
                    DocmostClient()
                assert "No API URL configured" in str(exc_info.value)

    def test_init_loads_url_from_config(self) -> None:
        """Client loads URL from config when not provided."""
        with patch("docmost.client.get_url", return_value="https://configured.com/api"):
            with patch("docmost.client.get_token", return_value="token"):
                client = DocmostClient()
                assert client.url == "https://configured.com/api"

    def test_init_loads_token_from_auth(self) -> None:
        """Client loads token from auth when not provided."""
        with patch("docmost.client.get_url", return_value="https://example.com/api"):
            with patch("docmost.client.get_token", return_value="stored-token"):
                client = DocmostClient()
                assert client.token == "stored-token"


class TestDocmostClientHeaders:
    """Tests for request headers."""

    def test_get_headers_with_token(self) -> None:
        """Headers include Authorization when token is present."""
        client = DocmostClient(url="https://example.com/api", token="my-token")
        headers = client._get_headers()
        assert headers["Authorization"] == "Bearer my-token"
        assert headers["Content-Type"] == "application/x-www-form-urlencoded"
        assert headers["Accept"] == "application/json"

    def test_get_headers_without_token(self) -> None:
        """Headers omit Authorization when no token."""
        with patch("docmost.client.get_token", return_value=None):
            client = DocmostClient(url="https://example.com/api", token=None)
            headers = client._get_headers()
            assert "Authorization" not in headers


class TestDocmostClientHandleResponse:
    """Tests for response handling and error mapping."""

    def test_handle_response_success(self) -> None:
        """Successful response returns JSON data."""
        client = DocmostClient(url="https://example.com/api", token="token")
        response = httpx.Response(200, json={"id": "123", "name": "Test"})
        result = client._handle_response(response)
        assert result == {"id": "123", "name": "Test"}

    def test_handle_response_401_raises_authentication_error(self) -> None:
        """401 response raises AuthenticationError."""
        client = DocmostClient(url="https://example.com/api", token="token")
        response = httpx.Response(401, json={"message": "Invalid token"})
        with pytest.raises(AuthenticationError) as exc_info:
            client._handle_response(response)
        assert exc_info.value.status_code == 401
        assert "Authentication failed" in str(exc_info.value)

    def test_handle_response_404_raises_not_found_error(self) -> None:
        """404 response raises NotFoundError."""
        client = DocmostClient(url="https://example.com/api", token="token")
        response = httpx.Response(404, json={"message": "Page not found"})
        with pytest.raises(NotFoundError) as exc_info:
            client._handle_response(response)
        assert exc_info.value.status_code == 404
        assert "Page not found" in str(exc_info.value)

    def test_handle_response_400_raises_validation_error(self) -> None:
        """400 response raises ValidationError."""
        client = DocmostClient(url="https://example.com/api", token="token")
        response = httpx.Response(400, json={"message": "Invalid input"})
        with pytest.raises(ValidationError) as exc_info:
            client._handle_response(response)
        assert exc_info.value.status_code == 400
        assert "Invalid input" in str(exc_info.value)

    def test_handle_response_500_raises_docmost_error(self) -> None:
        """500 response raises generic DocmostError."""
        client = DocmostClient(url="https://example.com/api", token="token")
        response = httpx.Response(500, json={"message": "Internal error"})
        with pytest.raises(DocmostError) as exc_info:
            client._handle_response(response)
        assert exc_info.value.status_code == 500
        assert "Internal error" in str(exc_info.value)

    def test_handle_response_invalid_json(self) -> None:
        """Non-JSON response falls back to text."""
        client = DocmostClient(url="https://example.com/api", token="token")
        response = httpx.Response(200, content=b"plain text")
        result = client._handle_response(response)
        assert result == {"error": "plain text"}

    def test_handle_response_error_without_message(self) -> None:
        """Error response without message uses default."""
        client = DocmostClient(url="https://example.com/api", token="token")
        response = httpx.Response(403, json={})
        with pytest.raises(DocmostError) as exc_info:
            client._handle_response(response)
        assert "API error: 403" in str(exc_info.value)


class TestDocmostClientPost:
    """Tests for POST requests."""

    def test_post_sends_json_data(self, httpx_mock) -> None:
        """POST request sends data as JSON."""
        httpx_mock.add_response(json={"result": "success"})
        client = DocmostClient(url="https://example.com/api", token="token")
        result = client.post("/test", {"key": "value"})
        assert result == {"result": "success"}

        request = httpx_mock.get_request()
        assert request.url == "https://example.com/api/test"
        assert request.method == "POST"
        assert request.headers["Content-Type"] == "application/json"

    def test_post_handles_trailing_slash(self, httpx_mock) -> None:
        """URL trailing slash is handled correctly."""
        httpx_mock.add_response(json={"ok": True})
        client = DocmostClient(url="https://example.com/api/", token="token")
        client.post("/endpoint", {})

        request = httpx_mock.get_request()
        assert request.url == "https://example.com/api/endpoint"

    def test_post_with_empty_data(self, httpx_mock) -> None:
        """POST with None data sends empty dict."""
        httpx_mock.add_response(json={"result": "ok"})
        client = DocmostClient(url="https://example.com/api", token="token")
        client.post("/test", None)

        request = httpx_mock.get_request()
        assert request.method == "POST"


class TestDocmostClientPostJson:
    """Tests for POST JSON requests."""

    def test_post_json_sends_json_content(self, httpx_mock) -> None:
        """POST JSON request sends JSON data."""
        httpx_mock.add_response(json={"result": "success"})
        client = DocmostClient(url="https://example.com/api", token="token")
        result = client.post_json("/test", {"key": "value"})
        assert result == {"result": "success"}

        request = httpx_mock.get_request()
        assert request.headers["Content-Type"] == "application/json"

    def test_post_json_with_empty_data(self, httpx_mock) -> None:
        """POST JSON with None data sends empty dict."""
        httpx_mock.add_response(json={"result": "ok"})
        client = DocmostClient(url="https://example.com/api", token="token")
        client.post_json("/test", None)

        request = httpx_mock.get_request()
        assert request.method == "POST"


class TestGetClient:
    """Tests for get_client factory function."""

    def test_get_client_returns_configured_client(self) -> None:
        """get_client returns a configured DocmostClient."""
        client = get_client(url="https://test.com/api", token="test-token")
        assert isinstance(client, DocmostClient)
        assert client.url == "https://test.com/api"
        assert client.token == "test-token"

    def test_get_client_with_defaults(self) -> None:
        """get_client uses defaults from config/auth."""
        with patch("docmost.client.get_url", return_value="https://default.com/api"):
            with patch("docmost.client.get_token", return_value="default-token"):
                client = get_client()
                assert client.url == "https://default.com/api"
                assert client.token == "default-token"


class TestDocmostErrorAttributes:
    """Tests for DocmostError exception attributes."""

    def test_docmost_error_has_status_code(self) -> None:
        """DocmostError stores status_code."""
        err = DocmostError("Test error", status_code=500)
        assert err.status_code == 500

    def test_docmost_error_has_response(self) -> None:
        """DocmostError stores response data."""
        response_data = {"error": "details"}
        err = DocmostError("Test error", response=response_data)
        assert err.response == response_data

    def test_authentication_error_is_docmost_error(self) -> None:
        """AuthenticationError is a DocmostError subclass."""
        err = AuthenticationError("Auth failed")
        assert isinstance(err, DocmostError)

    def test_not_found_error_is_docmost_error(self) -> None:
        """NotFoundError is a DocmostError subclass."""
        err = NotFoundError("Not found")
        assert isinstance(err, DocmostError)

    def test_validation_error_is_docmost_error(self) -> None:
        """ValidationError is a DocmostError subclass."""
        err = ValidationError("Invalid")
        assert isinstance(err, DocmostError)
