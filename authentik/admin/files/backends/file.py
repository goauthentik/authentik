import os
from collections.abc import Generator, Iterator
from contextlib import contextmanager
from pathlib import Path

from django.db import connection
from django.http.request import HttpRequest
from django.utils.functional import cached_property
from structlog.stdlib import get_logger

from authentik.admin.files.backends.base import ManageableBackend
from authentik.admin.files.usage import FileUsage
from authentik.lib.config import CONFIG

LOGGER = get_logger()


class FileBackend(ManageableBackend):
    """Local filesystem backend for file storage.

    Stores files in a local directory structure:
    - Path: {base_dir}/{usage}/{schema}/{filename}
    - Supports full file management (upload, delete, list)
    - Used when storage.backend=file (default)
    """

    name = "file"
    allowed_usages = list(FileUsage)  # All usages

    @cached_property
    def _base_dir(self) -> Path:
        return Path(
            CONFIG.get(
                f"storage.{self.usage.value}.{self.name}.path",
                CONFIG.get(f"storage.{self.name}.path", "./data"),
            )
        )

    @cached_property
    def base_path(self) -> Path:
        """Path structure: {base_dir}/{usage}/{schema}"""
        return self._base_dir / self.usage.value / connection.schema_name

    def supports_file(self, name: str) -> bool:
        """We support all file usages"""
        return True
        # return self.base_path.exists() and (
        #     self._base_dir.is_mount() or (self._base_dir / self.usage.value).is_mount()
        # )

    def list_files(self) -> Generator[str]:
        """List all files returning relative paths from base_path."""
        for root, _, files in os.walk(self.base_path):
            for file in files:
                full_path = Path(root) / file
                rel_path = full_path.relative_to(self.base_path)
                yield str(rel_path)

    def file_url(self, name: str, request: HttpRequest | None = None) -> str:
        """Get URL for accessing the file."""
        prefix = CONFIG.get("web.path", "/")[:-1]
        url = f"{prefix}/{self.usage.value}/{connection.schema_name}/{name}"
        if request is None:
            return url
        return request.build_absolute_uri(url)

    def save_file(self, name: str, content: bytes) -> None:
        """Save file to local filesystem."""
        path = self.base_path / Path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w+b") as f:
            f.write(content)

    @contextmanager
    def save_file_stream(self, name: str) -> Iterator:
        """Contxt manager for streaming file writes to local filesystem."""
        path = self.base_path / Path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            yield f

    def delete_file(self, name: str) -> None:
        """Delete file from local filesystem."""
        path = self.base_path / Path(name)
        path.unlink(missing_ok=True)

    def file_exists(self, name: str) -> bool:
        """Check if a file exists."""
        path = self.base_path / Path(name)
        return path.exists()
