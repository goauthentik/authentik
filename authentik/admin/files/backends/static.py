from collections.abc import Generator
from pathlib import Path

from django.http.request import HttpRequest

from authentik.admin.files.backends.base import Backend
from authentik.admin.files.usage import FileUsage
from authentik.lib.config import CONFIG

STATIC_ASSETS_BASE_DIR = Path("web/dist")
STATIC_ASSETS_DIRS = [Path(p) for p in ("assets/icons", "assets/images")]
STATIC_ASSETS_SOURCES_DIR = Path("web/authentik/sources")
STATIC_FILE_EXTENSIONS = [".svg", ".png", ".jpg", ".jpeg"]
STATIC_PATH_PREFIX = "/static"
# Must match src/server/static.rs
STATIC_SERVED_DIRS = {
    f"{STATIC_PATH_PREFIX}/dist/": STATIC_ASSETS_BASE_DIR,
    f"{STATIC_PATH_PREFIX}/authentik/": Path("web/authentik"),
}


class StaticBackend(Backend):
    """Read-only backend for static files from web/dist/assets.

    - Used for serving built-in static assets like icons and images.
    - Files cannot be uploaded or deleted through this backend.
    - Only accessible through resolve_file_url when a static path is detected.
    """

    allowed_usages = [FileUsage.MEDIA]

    def supports_file(self, name: str) -> bool:
        """Check if file path is a static path."""
        return name.startswith(STATIC_PATH_PREFIX)

    def list_files(self) -> Generator[str]:
        """List all static files."""
        # List built-in source icons
        if STATIC_ASSETS_SOURCES_DIR.exists():
            for file_path in STATIC_ASSETS_SOURCES_DIR.iterdir():
                if file_path.is_file() and (file_path.suffix in STATIC_FILE_EXTENSIONS):
                    yield f"{STATIC_PATH_PREFIX}/authentik/sources/{file_path.name}"

        # List other static assets
        for dir in STATIC_ASSETS_DIRS:
            dist_dir = STATIC_ASSETS_BASE_DIR / dir
            if dist_dir.exists():
                for file_path in dist_dir.rglob("*"):
                    if file_path.is_file() and (file_path.suffix in STATIC_FILE_EXTENSIONS):
                        yield f"{STATIC_PATH_PREFIX}/dist/{dir}/{file_path.name}"

    def file_url(
        self,
        name: str,
        request: HttpRequest | None = None,
        use_cache: bool = True,
    ) -> str:
        """Get URL for static file."""
        prefix = CONFIG.get("web.path", "/")[:-1]
        url = f"{prefix}{name}"
        if request is None:
            return url
        return request.build_absolute_uri(url)

    def read_file(self, name: str) -> bytes:
        """Read static file from the directory it is served from."""
        for prefix, directory in STATIC_SERVED_DIRS.items():
            if not name.startswith(prefix):
                continue
            base_path = directory.resolve()
            path = (base_path / name.removeprefix(prefix)).resolve()
            # Static paths skip file name validation, see FileBackend.read_file
            if path.is_relative_to(base_path):
                return path.read_bytes()
        raise FileNotFoundError(name)
