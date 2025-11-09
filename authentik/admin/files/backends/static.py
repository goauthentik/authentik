"""Static file backend for built-in assets"""

from collections.abc import Generator, Iterator
from pathlib import Path

from authentik.admin.files.backend import Backend, Usage
from authentik.admin.files.constants import (
    STATIC_ASSETS_DIRS,
    STATIC_FILE_EXTENSIONS,
    STATIC_PATH_PREFIX,
    STATIC_SOURCES_DIR,
)
from authentik.admin.files.utils import get_web_path_prefix


class StaticBackend(Backend):
    """Read-only backend for static files from web/dist/assets.

    - Used for serving built-in static assets like icons and images.
    - Files cannot be uploaded or deleted through this backend.
    - Only accessible through resolve_file_url when a static path is detected.
    """

    allowed_usages = [Usage.MEDIA]
    manageable = False

    def supports_file_path(self, file_path: str) -> bool:
        """Check if file path is a static path."""
        return file_path.startswith(STATIC_PATH_PREFIX) or file_path.startswith("web/dist/assets") # see service.py comment

    def list_files(self) -> Generator[str]:
        """List all static files."""
        # List built-in source icons
        if STATIC_SOURCES_DIR.exists():
            for file_path in STATIC_SOURCES_DIR.iterdir():
                if file_path.is_file() and (file_path.suffix in STATIC_FILE_EXTENSIONS):
                    yield f"{STATIC_PATH_PREFIX}/authentik/sources/{file_path.name}"

        # List other static assets
        for dir in STATIC_ASSETS_DIRS:
            dist_dir = Path(f"web/dist/{dir}")
            if dist_dir.exists():
                for file_path in dist_dir.rglob("*"):
                    if file_path.is_file() and (file_path.suffix in STATIC_FILE_EXTENSIONS):
                        yield f"{STATIC_PATH_PREFIX}/{dir}/{file_path.name}"

    def file_url(self, name: str) -> str:
        """Get URL for static file."""
        prefix = get_web_path_prefix()
        if name.startswith(STATIC_PATH_PREFIX):
            return prefix + name
        if name.startswith("web/dist/assets"):
            return f"{prefix}{STATIC_PATH_PREFIX}/dist/{name.removeprefix('web/dist/')}"
        raise ValueError(f"Invalid static file path: {name}")

    def file_size(self, name: str) -> int:
        """Static files size not tracked."""
        return 0

    def file_exists(self, name: str) -> bool:
        """Check if static file exists."""
        # Static files are assumed to exist if they match the pattern
        return self.supports_file_path(name)

    def save_file(self, name: str, content: bytes) -> None:
        """Not supported for static backend."""
        raise NotImplementedError("Cannot save files to static backend")

    def save_file_stream(self, name: str) -> Iterator:
        """Not supported for static backend."""
        raise NotImplementedError("Cannot save files to static backend")

    def delete_file(self, name: str) -> None:
        """Not supported for static backend."""
        raise NotImplementedError("Cannot delete files from static backend")
