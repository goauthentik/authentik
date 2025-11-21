from collections.abc import Generator, Iterator

from django.http.request import HttpRequest
from structlog.stdlib import get_logger

from authentik.admin.files.usage import FileUsage

LOGGER = get_logger()


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
        Check if this backend can handle the given file path pattern.

        Args:
            file_path: File path pattern to check

        Returns:
            True if this backend supports this file path pattern
        """
        raise NotImplementedError

    def list_files(self) -> Generator[str]:
        """
        List all files stored in this backend.

        Yields:
            Relative file paths
        """
        raise NotImplementedError

    def file_url(self, name: str, request: HttpRequest | None = None) -> str:
        """
        Get URL for accessing the file.

        Args:
            file_path: Relative file path
            request: Optional Django HttpRequest for fully qualifed URL building

        Returns:
            URL to access the file (may be relative or absolute depending on backend)
        """
        raise NotImplementedError


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
