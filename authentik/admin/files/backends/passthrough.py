"""Passthrough backend for external URLs or Font Awesome"""

from collections.abc import Generator, Iterator

from authentik.admin.files.backend import Backend, Usage
from authentik.admin.files.constants import EXTERNAL_URL_SCHEMES, FONT_AWESOME_SCHEME


class PassthroughBackend(Backend):
    """Passthrough backend for external URLs and special schemes.

    Handles external resources that aren't stored in authentik:
    - Font Awesome icons (fa://...)
    - HTTP/HTTPS URLs (http://..., https://...)

    Files that are "managed" by this backend are just passed through as-is.
    No upload, delete, or listing operations are supported.
    Only accessible through resolve_file_url when an external URL is detected.
    """

    allowed_usages = [Usage.MEDIA]
    manageable = False

    def supports_file_path(self, file_path: str) -> bool:
        """Check if file path is an external URL or Font Awesome icon."""
        if file_path.startswith(FONT_AWESOME_SCHEME):
            return True

        for scheme in EXTERNAL_URL_SCHEMES:
            if file_path.startswith(scheme):
                return True

        return False

    def list_files(self) -> Generator[str]:
        """External files cannot be listed."""
        yield from []

    def file_url(self, name: str) -> str:
        """Return the URL as-is for passthrough files."""
        return name

    def file_size(self, name: str) -> int:
        """External files size not tracked."""
        return 0

    def file_exists(self, name: str) -> bool:
        """External files are assumed to exist if they match the pattern."""
        return self.supports_file_path(name)

    def save_file(self, name: str, content: bytes) -> None:
        """Not supported for passthrough backend."""
        raise NotImplementedError("Cannot save files to passthrough backend")

    def save_file_stream(self, name: str) -> Iterator:
        """Not supported for passthrough backend."""
        raise NotImplementedError("Cannot save files to passthrough backend")

    def delete_file(self, name: str) -> None:
        """Not supported for passthrough backend."""
        raise NotImplementedError("Cannot delete files from passthrough backend")
