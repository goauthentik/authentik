"""Base backend interface and Usage enum"""

from abc import ABC, abstractmethod
from collections.abc import Generator, Iterator
from enum import Enum

from structlog.stdlib import get_logger

from authentik.admin.files.utils import get_storage_config

LOGGER = get_logger()


class Usage(str, Enum):
    """Usage types for file storage"""

    MEDIA = "media"
    REPORTS = "reports"


class Backend(ABC):
    """Base class for file storage backends.

    Class attributes:
        allowed_usages: List of Usage types this backend can handle
        manageable: Whether files can be uploaded/deleted through the API
    """

    allowed_usages: list[Usage] = []
    manageable: bool = True

    @classmethod
    def get_allowed_api_usages(cls) -> list[Usage]:
        """Get usages that can be accessed via the files API.

        Returns:
            List of Usage types that are both allowed and manageable
        """
        return [u for u in cls.allowed_usages if cls.manageable]

    def __init__(self, usage: Usage):
        """Initialize backend for the given usage type.

        Args:
            usage: Usage type enum value
        """
        self.usage = usage
        # Only get backend config for manageable backends
        if self.manageable:
            self._backend_type = get_storage_config(usage, "backend", "file")
            LOGGER.info(
                "Initialized storage backend",
                backend=self.__class__.__name__,
                usage=usage.value,
                backend_type=self._backend_type,
            )
        else:
            self._backend_type = None

    def get_config(self, key: str, default=None):
        """Get configuration value with usage-specific override support.

        Args:
            key: Configuration key to look up
            default: Default value if not found

        Returns:
            Configuration value
        """
        return get_storage_config(self.usage, key, default)

    @abstractmethod
    def supports_file_path(self, file_path: str) -> bool:
        """Check if this backend can handle the given file path pattern.

        Args:
            file_path: File path pattern to check

        Returns:
            True if this backend supports this file path pattern
        """
        pass

    @abstractmethod
    def list_files(self) -> Generator[str]:
        """List all files managed by this backend.

        Yields:
            Relative file paths
        """
        pass

    @abstractmethod
    def save_file(self, name: str, content: bytes) -> None:
        """Save file content to storage.

        Args:
            name: Relative file path
            content: File content as bytes
        """
        pass

    @abstractmethod
    def save_file_stream(self, name: str) -> Iterator:
        """Context manager for streaming file writes.

        Args:
            name: Relative file path

        Returns:
            Context manager that yields a writable file-like object

        Usage:
            with backend.save_file_stream("output.csv") as f:
                f.write(b"data...")
        """
        pass

    @abstractmethod
    def delete_file(self, name: str) -> None:
        """Delete file from storage.

        Args:
            name: Relative file path
        """
        pass

    @abstractmethod
    def file_url(self, name: str) -> str:
        """Get URL for accessing the file.

        Args:
            name: Relative file path

        Returns:
            URL to access the file (may be relative or absolute depending on backend)
        """
        pass

    @abstractmethod
    def file_size(self, name: str) -> int:
        """Get file size in bytes.

        Args:
            name: Relative file path

        Returns:
            File size in bytes, or 0 if file doesn't exist
        """
        pass

    @abstractmethod
    def file_exists(self, name: str) -> bool:
        """Check if a file exists.

        Args:
            name: Relative file path

        Returns:
            True if file exists, False otherwise
        """
        pass


def get_allowed_api_usages() -> list[Usage]:
    """Get list of usages that are accessible via the files API.

    Returns:
        List of allowed Usage types for API access
    """
    return [Usage.MEDIA]
