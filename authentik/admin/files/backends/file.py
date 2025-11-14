"""Local filesystem storage backend"""

import os
from collections.abc import Generator, Iterator
from contextlib import contextmanager
from pathlib import Path

from django.db import connection
from structlog.stdlib import get_logger

from authentik.admin.files.backend import Backend, Usage
from authentik.admin.files.utils import get_web_path_prefix

LOGGER = get_logger()


class FileBackend(Backend):
    """Local filesystem backend for file storage.

    Stores files in a local directory structure:
    - Path: {base_dir}/{usage}/{schema}/{filename}
    - Supports full file management (upload, delete, list)
    - Used when storage.backend=file (default)
    """

    allowed_usages = list(Usage)  # All usages
    manageable = True

    @property
    def base_path(self) -> Path:
        """Path structure: {base_dir}/{usage}/{schema}"""
        # TODO: There must be a better way of doing this? ./data in local dev with
        # /data in containers, tho containers might still use ./data since
        # it's the "default" value
        file_path = self.get_config("file.path", "/data")
        base_dir = Path(file_path)
        result = base_dir / self.usage.value / connection.schema_name

        LOGGER.info(
            "File storage base path resolved",
            usage=self.usage.value,
            schema=connection.schema_name,
            path=str(result),
        )
        return result

    def supports_file_path(self, file_path: str) -> bool:
        """Check if this backend type is configured."""
        return self._backend_type == "file"

    def list_files(self) -> Generator[str]:
        """List all files returning relative paths from base_path."""
        base_path = self.base_path

        if not base_path.exists():
            LOGGER.warning(
                "File storage path does not exist",
                usage=self.usage.value,
                schema=connection.schema_name,
                path=str(base_path),
            )
            return

        file_count = 0
        for root, _, files in os.walk(base_path):
            for file in files:
                full_path = Path(root) / file
                rel_path = full_path.relative_to(base_path)
                file_count += 1
                yield str(rel_path)

        LOGGER.info(
            "Listed files from storage",
            usage=self.usage.value,
            schema=connection.schema_name,
            count=file_count,
        )

    def save_file(self, name: str, content: bytes) -> None:
        """Save file to local filesystem."""
        path = self.base_path / Path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
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

    def file_url(self, name: str) -> str:
        """Get URL for accessing the file."""
        prefix = get_web_path_prefix()
        return f"{prefix}/static/{self.usage.value}/{connection.schema_name}/{name}"

    def file_size(self, name: str) -> int:
        """Get file size in bytes."""
        path = self.base_path / Path(name)
        try:
            return path.stat().st_size if path.exists() else 0
        except (OSError, ValueError):
            return 0

    def file_exists(self, name: str) -> bool:
        """Check if a file exists."""
        path = self.base_path / Path(name)
        return path.exists()
