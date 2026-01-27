import mimetypes
from collections.abc import Callable, Generator, Iterator
from typing import cast

from django.core.cache import cache
from django.http.request import HttpRequest
from structlog.stdlib import get_logger

from authentik.admin.files.usage import FileUsage

CACHE_PREFIX = "goauthentik.io/admin/files"
LOGGER = get_logger()

# Theme variable placeholder for theme-specific files like logo-%(theme)s.png
THEME_VARIABLE = "%(theme)s"


def get_content_type(name: str) -> str:
    """Get MIME type for a file based on its extension."""
    content_type, _ = mimetypes.guess_type(name)
    return content_type or "application/octet-stream"


def get_valid_themes() -> list[str]:
    """Get valid themes that can be substituted for %(theme)s."""
    from authentik.brands.api import Themes

    return [t.value for t in Themes if t != Themes.AUTOMATIC]


def has_theme_variable(name: str) -> bool:
    """Check if filename contains %(theme)s variable."""
    return THEME_VARIABLE in name


def substitute_theme(name: str, theme: str) -> str:
    """Replace %(theme)s with the given theme."""
    return name.replace(THEME_VARIABLE, theme)


class Backend:
    """
    Base class for file storage backends.

    Class attributes:
        allowed_usages: List of usages that can be used with this backend
    """

    allowed_usages: list[FileUsage]

    def __init__(self, usage: FileUsage):
        """
        Initialize backend for the given usage type.

        Args:
            usage: FileUsage type enum value
        """
        self.usage = usage
        LOGGER.debug(
            "Initializing storage backend",
            backend=self.__class__.__name__,
            usage=usage.value,
        )

    def supports_file(self, name: str) -> bool:
        """
        Check if this backend can handle the given file path.

        Args:
            name: File path to check

        Returns:
            True if this backend supports this file path
        """
        raise NotImplementedError

    def list_files(self) -> Generator[str]:
        """
        List all files stored in this backend.

        Yields:
            Relative file paths
        """
        raise NotImplementedError

    def file_url(
        self,
        name: str,
        request: HttpRequest | None = None,
        use_cache: bool = True,
    ) -> str:
        """
        Get URL for accessing the file.

        Args:
            file_path: Relative file path
            request: Optional Django HttpRequest for fully qualifed URL building
            use_cache: whether to retrieve the URL from cache

        Returns:
            URL to access the file (may be relative or absolute depending on backend)
        """
        raise NotImplementedError

    def themed_urls(
        self,
        name: str,
        request: HttpRequest | None = None,
    ) -> dict[str, str] | None:
        """
        Get URLs for each theme variant when filename contains %(theme)s.

        Args:
            name: File path potentially containing %(theme)s
            request: Optional Django HttpRequest for URL building

        Returns:
            Dict mapping theme to URL if %(theme)s present, None otherwise
        """
        if not has_theme_variable(name):
            return None

        return {
            theme: self.file_url(substitute_theme(name, theme), request, use_cache=True)
            for theme in get_valid_themes()
        }


class ManageableBackend(Backend):
    """
    Base class for manageable file storage backends.

    Class attributes:
        name: Canonical name of the storage backend, for use in configuration.
    """

    name: str

    @property
    def manageable(self) -> bool:
        """
        Whether this backend can actually be used for management.

        Used only for management check, not for created the backend
        """
        raise NotImplementedError

    def save_file(self, name: str, content: bytes) -> None:
        """
        Save file content to storage.

        Args:
            file_path: Relative file path
            content: File content as bytes
        """
        raise NotImplementedError

    def save_file_stream(self, name: str) -> Iterator:
        """
        Context manager for streaming file writes.

        Args:
            file_path: Relative file path

        Returns:
            Context manager that yields a writable file-like object

        FileUsage:
            with backend.save_file_stream("output.csv") as f:
                f.write(b"data...")
        """
        raise NotImplementedError

    def delete_file(self, name: str) -> None:
        """
        Delete file from storage.

        Args:
            file_path: Relative file path
        """
        raise NotImplementedError

    def file_exists(self, name: str) -> bool:
        """
        Check if a file exists.

        Args:
            file_path: Relative file path

        Returns:
            True if file exists, False otherwise
        """
        raise NotImplementedError

    def _cache_get_or_set(
        self,
        name: str,
        request: HttpRequest | None,
        default: Callable[[str, HttpRequest | None], str],
        timeout: int,
    ) -> str:
        timeout_ignore = 60
        timeout = int(timeout * 0.67)
        if timeout < timeout_ignore:
            timeout = 0

        request_key = "None"
        if request is not None:
            request_key = f"{request.build_absolute_uri('/')}"
        cache_key = f"{CACHE_PREFIX}/{self.name}/{self.usage}/{request_key}/{name}"

        return cast(str, cache.get_or_set(cache_key, lambda: default(name, request), timeout))
