from collections.abc import Generator
from pathlib import Path, PurePosixPath

from django.conf import settings
from django.http.request import HttpRequest

from authentik.admin.files.backends.base import THEME_VARIABLE, Backend, get_valid_themes
from authentik.admin.files.usage import FileUsage
from authentik.lib.config import CONFIG

STATIC_ASSETS_BASE_DIR = Path("web/dist")
STATIC_ASSETS_DIRS = [Path(p) for p in ("assets/icons", "assets/images")]
STATIC_ASSETS_SOURCES_DIR = Path("web/authentik/sources")
STATIC_FILE_EXTENSIONS = [".svg", ".png", ".jpg", ".jpeg"]
STATIC_PATH_PREFIX = "/static"
STATIC_SOURCES_PREFIX = f"{STATIC_PATH_PREFIX}/authentik/sources/"


def static_url_name(url: str | None) -> str | None:
    """Name of the static file behind a URL from Django's ``static()``, as this backend
    names it. Models use ``static()`` for their default icons."""
    if not url or not url.startswith(settings.STATIC_URL):
        return None
    return f"{STATIC_PATH_PREFIX}/{url.removeprefix(settings.STATIC_URL)}"


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
        # List built-in source icons, one folder per icon with a variant per theme
        if STATIC_ASSETS_SOURCES_DIR.exists():
            for icon_dir in STATIC_ASSETS_SOURCES_DIR.iterdir():
                if not icon_dir.is_dir():
                    continue
                for light in icon_dir.glob("light.*"):
                    if light.suffix in STATIC_FILE_EXTENSIONS:
                        icon = f"{icon_dir.name}/{THEME_VARIABLE}{light.suffix}"
                        yield f"{STATIC_SOURCES_PREFIX}{icon}"

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

    def themed_urls(
        self,
        name: str,
        request: HttpRequest | None = None,
        use_cache: bool = True,
    ) -> dict[str, str] | None:
        """Theme variants of ``%(theme)s`` files, and of a single variant of a built-in
        source icon, such as ``github/light.svg``, which models use as default icons."""
        path = PurePosixPath(name)
        if path.parent.parent == PurePosixPath(STATIC_SOURCES_PREFIX) and (
            path.stem in get_valid_themes()
        ):
            name = str(path.with_stem(THEME_VARIABLE))
        return super().themed_urls(name, request, use_cache=use_cache)
