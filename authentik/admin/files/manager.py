from collections.abc import Generator, Iterable, Iterator
from contextlib import contextmanager

from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.db import DatabaseError
from django.http.request import HttpRequest
from rest_framework.request import Request
from structlog.stdlib import get_logger

from authentik.admin.files.backends.base import (
    PREFETCHED_URLS,
    ManageableBackend,
    get_valid_themes,
    has_theme_variable,
    substitute_theme,
)
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
        return self.management_backend is not None and self.management_backend.manageable

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
        use_cache: bool = True,
    ) -> str:
        """
        Get URL for accessing the file.

        Set ``use_cache=False`` when the caller needs a fresh signed URL instead
        of a cached one, for example when serializing flow/login payloads that
        may be refreshed after the previous JWT has expired.

        A name with ``%(theme)s`` resolves to its light variant, so the URL always
        points at a real file. Callers that know the theme use ``themed_urls()``.
        """
        if not name:
            return ""

        if isinstance(request, Request):
            request = request._request

        name = substitute_theme(name, "light")
        for backend in self.backends:
            if backend.supports_file(name):
                return backend.file_url(name, request, use_cache=use_cache)

        LOGGER.warning(f"Could not find file backend for file: {name}")
        return ""

    def themed_urls(
        self,
        name: str | None,
        request: HttpRequest | Request | None = None,
        use_cache: bool = True,
    ) -> dict[str, str] | None:
        """
        Get URLs for each theme variant when filename contains %(theme)s, or when it is
        one variant of a built-in source icon.

        ``use_cache`` has the same semantics as ``file_url()`` and allows
        callers to force regeneration of expiring signed URLs.

        Returns dict mapping theme to URL if there are theme variants, None otherwise.
        """
        if not name:
            return None

        if isinstance(request, Request):
            request = request._request

        for backend in self.backends:
            if backend.supports_file(name):
                return backend.themed_urls(name, request, use_cache=use_cache)

        return None

    @contextmanager
    def prefetch_urls(self, names: Iterable[str | None]) -> Iterator[None]:
        """
        Read the cached URLs of ``names`` and their theme variants with one query, for the
        ``file_url()`` and ``themed_urls()`` calls made without a request inside this block.
        Each of those calls otherwise reads the cache with a query of its own, which a list
        of objects with icons makes once per object.

        A URL that is not cached yet is generated and cached by its own call, as without
        this block.
        """
        keys = []
        for name in names:
            if not name:
                continue
            variants = [substitute_theme(name, "light")]
            if has_theme_variable(name):
                variants += [substitute_theme(name, theme) for theme in get_valid_themes()]
            for variant in variants:
                backend = next((b for b in self.backends if b.supports_file(variant)), None)
                # Only the manageable backends cache their URLs
                if isinstance(backend, ManageableBackend):
                    keys.append(backend._cache_key(variant, None))
        try:
            prefetched = cache.get_many(keys)
        except DatabaseError:
            # cache.get() treats a failing cache as empty; do the same, so each call reads or
            # generates its own URL
            prefetched = {}
        token = PREFETCHED_URLS.set(prefetched)
        try:
            yield
        finally:
            PREFETCHED_URLS.reset(token)

    def _check_manageable(self) -> None:
        if not self.manageable:
            raise ImproperlyConfigured("No file management backend configured.")

    def save_file(self, file_path: str, content: bytes) -> None:
        """
        Save file contents to storage.
        """
        self._check_manageable()
        assert self.management_backend is not None  # nosec
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
        assert self.management_backend is not None  # nosec
        return self.management_backend.save_file_stream(file_path)

    def delete_file(self, file_path: str) -> None:
        """
        Delete file from storage.
        """
        self._check_manageable()
        assert self.management_backend is not None  # nosec
        return self.management_backend.delete_file(file_path)

    def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists.
        """
        self._check_manageable()
        assert self.management_backend is not None  # nosec
        return self.management_backend.file_exists(file_path)


MANAGERS = {usage: FileManager(usage) for usage in list(FileUsage)}


def get_file_manager(usage: FileUsage) -> FileManager:
    return MANAGERS[usage]
