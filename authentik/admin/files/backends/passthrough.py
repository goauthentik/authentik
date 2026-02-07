from collections.abc import Generator

from django.http.request import HttpRequest

from authentik.admin.files.backends.base import Backend
from authentik.admin.files.usage import FileUsage

EXTERNAL_URL_SCHEMES = ["http:", "https://"]
FONT_AWESOME_SCHEME = "fa://"


class PassthroughBackend(Backend):
    """Passthrough backend for external URLs and special schemes.

    Handles external resources that aren't stored in authentik:
    - Font Awesome icons (fa://...)
    - HTTP/HTTPS URLs (http://..., https://...)

    Files that are "managed" by this backend are just passed through as-is.
    No upload, delete, or listing operations are supported.
    Only accessible through resolve_file_url when an external URL is detected.
    """

    allowed_usages = [FileUsage.MEDIA]

    def supports_file(self, name: str) -> bool:
        """Check if file path is an external URL or Font Awesome icon."""
        if name.startswith(FONT_AWESOME_SCHEME):
            return True

        for scheme in EXTERNAL_URL_SCHEMES:
            if name.startswith(scheme):
                return True

        return False

    def list_files(self) -> Generator[str]:
        """External files cannot be listed."""
        yield from []

    def file_url(
        self,
        name: str,
        request: HttpRequest | None = None,
        use_cache: bool = True,
    ) -> str:
        """Return the URL as-is for passthrough files."""
        return name

    def themed_urls(
        self,
        name: str,
        request: HttpRequest | None = None,
    ) -> dict[str, str] | None:
        """Support themed URLs for external URLs with %(theme)s placeholder.

        If the external URL contains %(theme)s, substitute it for each theme.
        We can't verify that themed variants exist at the external location,
        but we trust the user to provide valid URLs.
        """
        from authentik.admin.files.backends.base import (
            get_valid_themes,
            has_theme_variable,
            substitute_theme,
        )

        if not has_theme_variable(name):
            return None

        return {theme: substitute_theme(name, theme) for theme in get_valid_themes()}
