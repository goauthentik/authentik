"""Utility functions for file handling"""

import mimetypes
from typing import TYPE_CHECKING, Any, Union

from django.db import connection
from django.http import HttpRequest

from authentik.lib.config import CONFIG

if TYPE_CHECKING:
    from rest_framework.request import Request



class RequestWrapper:
    """Wrapper to handle both Django HttpRequest and DRF Request objects."""

    def __init__(self, request: Union[HttpRequest, "Request"] | None = None):
        """Initialize RequestWrapper.

        Args:
            request: Django HttpRequest, DRF Request, or None
        """
        self._request = request

    @property
    def host(self) -> str | None:
        """Get the host from the request.

        Returns:
            Host string or None if no request
        """
        if not self._request:
            return None

        try:
            # DRF Request has _request attribute
            if hasattr(self._request, "_request"):
                return self._request._request.get_host()
            # Django HttpRequest
            return self._request.get_host()
        except (AttributeError, TypeError):
            return None

    @property
    def scheme(self) -> str:
        """Get the scheme from the request.

        Returns:
            'https' or 'http', defaults to 'https' if no request
        """
        if not self._request:
            return "https"

        try:
            # DRF Request
            if hasattr(self._request, "_request"):
                return "https" if self._request._request.is_secure() else "http"
            # Django HttpRequest
            return "https" if self._request.is_secure() else "http"
        except (AttributeError, TypeError):
            return "https"

    def build_absolute_uri(self, path: str) -> str:
        """Build an absolute URI from a relative path.

        Args:
            path: Relative path (e.g., "/static/icon.png")

        Returns:
            Absolute URL with scheme and host, or relative path if no request
        """
        if self.host:
            return f"{self.scheme}://{self.host}{path}"
        return path


def get_storage_config(key: str, default: Any = None) -> Any:
    """Get storage configuration.

    Storage configuration is shared across all usages (media, reports).
    The usage type only affects the path prefix in storage.

    Args:
        key: Configuration key
        default: Default value if not found

    Returns:
        Configuration value from storage.{key} or default

    Example:
        get_storage_config("s3.bucket_name")
        -> looks up storage.s3.bucket_name
    """
    storage_key = f"storage.{key}"
    return CONFIG.get(storage_key, default)


def get_mime_from_filename(filename: str) -> str:
    """Get MIME type from filename.

    Args:
        filename: Name of the file

    Returns:
        MIME type string
    """
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"


def get_web_path_prefix() -> str:
    """Get the web path prefix from configuration .

    Returns:
        Web path prefix without trailing slash (e.g., "" or "/authentik")
    """
    return CONFIG.get("web.path", "/")[:-1]


def get_schema_name() -> str:
    """Get the current database schema name (useful for tenanting).

    Returns:
        Schema name (e.g., "public")
    """
    return connection.schema_name


def strip_schema_prefix(file_path: str) -> str:
    """Strip schema prefix from file path if present.

    This is what we store in the database.

    Args:
        file_path: File path possibly with schema prefix (e.g., "public/my-icon.png")

    Returns:
        File path without schema prefix (e.g., "my-icon.png")
    """
    schema_prefix = f"{get_schema_name()}/"
    return file_path.removeprefix(schema_prefix)


def add_schema_prefix(file_path: str) -> str:
    """Add schema prefix to file path for display purposes.

    This is what we use to build the URLs and what we render in the UI.

    Args:
        file_path: Relative file path (e.g., "my-icon.png")

    Returns:
        File path with schema prefix (e.g., "public/my-icon.png")
    """
    return f"{get_schema_name()}/{file_path}"
