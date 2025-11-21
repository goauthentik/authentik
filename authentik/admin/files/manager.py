from collections.abc import Generator, Iterator

from django.core.exceptions import ImproperlyConfigured
from django.http.request import HttpRequest
from rest_framework.request import Request
from structlog.stdlib import get_logger

from authentik.admin.files.backends.base import ManageableBackend
from authentik.admin.files.backends.file import FileBackend
from authentik.admin.files.backends.passthrough import PassthroughBackend
from authentik.admin.files.backends.s3 import S3Backend
from authentik.admin.files.backends.static import StaticBackend
from authentik.admin.files.usage import FileUsage
from authentik.lib.config import CONFIG

LOGGER = get_logger()


_FILE_BACKENDS = [
    StaticBackend,
    PassthroughBackend,
    FileBackend,
    S3Backend,
]


class FileManager:
    def __init__(self, usage: FileUsage) -> None:
        management_backend_name = CONFIG.get(
            f"storage.{usage.value}.backend",
            CONFIG.get("storage.backend", "file"),
        )

        self.management_backend = None
        for backend in _FILE_BACKENDS:
            if issubclass(backend, ManageableBackend) and backend.name == management_backend_name:
                self.management_backend = backend(usage)
        if self.management_backend is None:
            LOGGER.warning(
                f"Storage backend configuration for {usage.value} is "
                f"invalid: {management_backend_name}"
            )

        self.backends = []
        for backend in _FILE_BACKENDS:
            if usage not in backend.allowed_usages:
                continue
            if isinstance(self.management_backend, backend):
                self.backends.append(self.management_backend)
            elif not issubclass(backend, ManageableBackend):
                self.backends.append(backend(usage))

    @property
    def manageable(self) -> bool:
        """
        Whether this file manager is able to manage files.
        """
        return self.management_backend is not None

    def list_files(self, manageable_only: bool = False) -> Generator[str]:
        """
        List available files.
        """
        for backend in self.backends:
            if manageable_only and not isinstance(backend, ManageableBackend):
                continue
            yield from backend.list_files()

    def file_url(
        self,
        name: str | None,
        request: HttpRequest | Request | None = None,
    ) -> str:
        """
        Get URL for accessing the file.
        """
        if not name:
            return ""

        if isinstance(request, Request):
            request = request._request

        for backend in self.backends:
            if backend.supports_file(name):
                return backend.file_url(name, request)

        LOGGER.warning(f"Could not find file backend for file: {name}")
        return ""

    def _check_manageable(self) -> None:
        if not self.manageable:
            raise ImproperlyConfigured("No file management backend configured.")

    def save_file(self, file_path: str, content: bytes) -> None:
        """
        Save file contents to storage.
        """
        self._check_manageable()
        assert self.management_backend is not None
        return self.management_backend.save_file(file_path, content)

    def save_file_stream(self, file_path: str) -> Iterator:
        """
        Context manager for streaming file writes.

        Args:
            file_path: Relative file path

        Returns:
            Context manager that yields a writable file-like object

        Usage:
            with manager.save_file_stream("output.csv") as f:
                f.write(b"data...")
        """
        self._check_manageable()
        assert self.management_backend is not None
        return self.management_backend.save_file_stream(file_path)

    def delete_file(self, file_path: str) -> None:
        """
        Delete file from storage.
        """
        self._check_manageable()
        assert self.management_backend is not None
        return self.management_backend.delete_file(file_path)

    def file_size(self, file_path: str) -> int:
        """
        Get file size in bytes.
        """
        self._check_manageable()
        assert self.management_backend is not None
        return self.management_backend.file_size(file_path)

    def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists.
        """
        self._check_manageable()
        assert self.management_backend is not None
        return self.management_backend.file_exists(file_path)
