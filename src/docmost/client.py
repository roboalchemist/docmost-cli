"""HTTP client for Docmost API."""

from typing import Any

import httpx

from docmost.auth import get_token
from docmost.config import get_url


class DocmostError(Exception):
    """Base exception for Docmost API errors."""

    def __init__(self, message: str, status_code: int | None = None, response: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class AuthenticationError(DocmostError):
    """Raised when authentication fails."""

    pass


class NotFoundError(DocmostError):
    """Raised when a resource is not found."""

    pass


class ValidationError(DocmostError):
    """Raised when request validation fails."""

    pass


class DocmostClient:
    """HTTP client for the Docmost API."""

    def __init__(self, url: str | None = None, token: str | None = None, timeout: float = 30.0):
        """Initialize the client.

        Args:
            url: Base URL for the API. If not provided, loads from config.
            token: Access token. If not provided, loads from auth storage.
            timeout: Request timeout in seconds.
        """
        self.url = url or get_url()
        self.token = token or get_token()
        self.timeout = timeout

        if not self.url:
            raise DocmostError("No API URL configured. Set DOCMOST_URL or run 'docmost login'.")

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with authentication."""
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle API response and raise appropriate errors."""
        try:
            data = response.json()
        except Exception:
            data = {"error": response.text}

        if response.status_code == 401:
            raise AuthenticationError(
                "Authentication failed. Please run 'docmost login'.",
                status_code=401,
                response=data,
            )

        if response.status_code == 404:
            raise NotFoundError(
                data.get("message", "Resource not found"),
                status_code=404,
                response=data,
            )

        if response.status_code == 400:
            raise ValidationError(
                data.get("message", "Validation error"),
                status_code=400,
                response=data,
            )

        if response.status_code >= 400:
            raise DocmostError(
                data.get("message", f"API error: {response.status_code}"),
                status_code=response.status_code,
                response=data,
            )

        # Unwrap response: {"data": {...}, "success": true, "status": 200} -> {...}
        if "data" in data and "success" in data and "status" in data:
            return data["data"]

        return data

    def post(self, endpoint: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make a POST request to the API with JSON body.

        Args:
            endpoint: API endpoint (e.g., "/spaces/list")
            data: Request body data

        Returns:
            API response as dictionary
        """
        url = f"{self.url.rstrip('/')}{endpoint}"

        headers = self._get_headers()
        headers["Content-Type"] = "application/json"

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                url,
                json=data or {},
                headers=headers,
            )
            return self._handle_response(response)

    def post_json(self, endpoint: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make a POST request with JSON body.

        Some endpoints may require JSON instead of urlencoded.

        Args:
            endpoint: API endpoint
            data: Request body data

        Returns:
            API response as dictionary
        """
        url = f"{self.url.rstrip('/')}{endpoint}"

        headers = self._get_headers()
        headers["Content-Type"] = "application/json"

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                url,
                json=data or {},
                headers=headers,
            )
            return self._handle_response(response)

    def upload_file(
        self, endpoint: str, file_path: str, form_data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Upload a file to the API with multipart/form-data.

        Args:
            endpoint: API endpoint (e.g., "/pages/import")
            file_path: Path to file to upload
            form_data: Additional form fields to send

        Returns:
            API response as dictionary
        """
        import os

        url = f"{self.url.rstrip('/')}{endpoint}"

        # Auth header only (no Content-Type, httpx will set it for multipart)
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        with open(file_path, "rb") as f:
            filename = os.path.basename(file_path)
            files = {"file": (filename, f, "text/markdown")}

            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    url,
                    files=files,
                    data=form_data or {},
                    headers=headers,
                )
                return self._handle_response(response)


def get_client(url: str | None = None, token: str | None = None) -> DocmostClient:
    """Get a configured Docmost client.

    Args:
        url: Optional API URL override
        token: Optional token override

    Returns:
        Configured DocmostClient instance
    """
    return DocmostClient(url=url, token=token)
