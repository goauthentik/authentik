"""Service layer for file operations + URL resolution."""

from django.http import HttpRequest

from authentik.admin.files.backend import Usage
from authentik.admin.files.constants import (
    EXTERNAL_URL_SCHEMES,
    FONT_AWESOME_SCHEME,
    STATIC_PATH_PREFIX,
)
from authentik.admin.files.factory import BackendFactory
from authentik.admin.files.utils import RequestWrapper, strip_schema_prefix


def resolve_file_url(file_path: str, usage: Usage) -> str:
    """Resolve a file path to it's URL using the appropriate backend.

    Args:
        file_path: The file path to resolve
        usage: Usage type to determine which backend to use

    Returns:
        Absolute URL for the file

    Handles:
    - Static files (/static/...)
    - Passthrough URLs (fa://, http://, https://...)
    - Storage files (uploaded files from the specified usage backend)

    Note: Returns relative URLs for FileBackend. Use resolve_file_url_full()
    for full URLs with domain.
    """
    if not file_path:
        return file_path

    # Passthrough backend for external URLs and Font Awesome
    if file_path.startswith(FONT_AWESOME_SCHEME):
        backend = BackendFactory.get_passthrough_backend(usage)
        return backend.file_url(file_path)

    for scheme in EXTERNAL_URL_SCHEMES:
        if file_path.startswith(scheme):
            backend = BackendFactory.get_passthrough_backend(usage)
            return backend.file_url(file_path)

    # Static backend for built-in static files
    if file_path.startswith(STATIC_PATH_PREFIX) or file_path.startswith("web/dist/assets"):
        #                                           ^^ todo: add to constants.py?? backends/static.py + more prob
        backend = BackendFactory.get_static_backend(usage)
        return backend.file_url(file_path)

    # Storage backend for uploaded files and strip schema prefix if present
    file_path = strip_schema_prefix(file_path)
    backend = BackendFactory.create(usage)
    return backend.file_url(file_path)

# TODO we could mabye pass boolean needs_full_url instead of duplicating this function
def resolve_file_url_full(
    file_path: str,
    usage: Usage,
    request: HttpRequest | None = None,
) -> str:
    """Resolve a file path to its FULL URL ,including scheme and domain.

    Args:
        file_path: The file path to resolve
        usage: Usage type to determine which backend to use
        request: Optional HTTP request for extracting host information

    Returns:
        Full URL with domain for uploaded files, relative URL if no request

    Handles:
    - Static files (/static/...) - returns full URL with domain
    - Passthrough URLs (fa://, http://, https://...) - returns as-is
    - Storage files - returns full URL for FileBackend, presigned URL for S3Backend

    This function builds complete URLs including scheme and domain, suitable for
    API responses where the consumer needs an absolute URL.
    """
    if not file_path:
        return file_path

    # Passthrough backend for external URLs and Font Awesome so we return as-is
    if file_path.startswith(FONT_AWESOME_SCHEME):
        backend = BackendFactory.get_passthrough_backend(usage)
        return backend.file_url(file_path)

    for scheme in EXTERNAL_URL_SCHEMES:
        if file_path.startswith(scheme):
            backend = BackendFactory.get_passthrough_backend(usage)
            return backend.file_url(file_path)

    # Wrap request for consistent interface
    request_wrapper = RequestWrapper(request)

    # Static backend for built-in static files
    if file_path.startswith(STATIC_PATH_PREFIX) or file_path.startswith("web/dist/assets"):
        backend = BackendFactory.get_static_backend(usage)
        relative_url = backend.file_url(file_path)
        return request_wrapper.build_absolute_uri(relative_url)

    # Storage backend for uploaded files - strip schema prefix if present
    file_path = strip_schema_prefix(file_path)
    backend = BackendFactory.create(usage)
    url = backend.file_url(file_path)

    # For S3Backend, file_url already returns a full presigned URL
    # For FileBackend, we need to prepend the scheme and host
    from authentik.admin.files.backends import FileBackend

    if request_wrapper.host and isinstance(backend, FileBackend):
        if not url.startswith("http"):
            return request_wrapper.build_absolute_uri(url)

    return url


def is_file_path_supported(file_path: str, backend_type: str) -> bool:
    """Check if a file path pattern is supported by a backend type.

    Args:
        file_path: File path pattern to check
        backend_type: Backend type identifier

    Returns:
        True if the backend supports this file path pattern

    Example:
        >>> is_file_path_supported("/static/icon.png", "static")
        True
        >>> is_file_path_supported("my-file.png", "file")
        True
        >>> is_file_path_supported("fa://fa-icon", "passthrough")
        True
    """
    if backend_type == "static":
        return file_path.startswith(STATIC_PATH_PREFIX) or file_path.startswith("web/dist/assets")

    if backend_type == "passthrough":
        if file_path.startswith(FONT_AWESOME_SCHEME):
            return True
        for scheme in EXTERNAL_URL_SCHEMES:
            if file_path.startswith(scheme):
                return True
        return False

    # For file/s3 backends, any path that's not static or passthrough
    return not is_file_path_supported(file_path, "static") and not is_file_path_supported(
        file_path, "passthrough"
    )
