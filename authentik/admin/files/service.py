"""Service layer for file operations + URL resolution."""

from django.http import HttpRequest

from authentik.admin.files.usage import FileUsage


def resolve_file_url(file_path: str, usage: FileUsage) -> str:
    """Resolve a file path to it's URL using the appropriate backend.

    Args:
        file_path: The file path to resolve
        usage: FileUsage type to determine which backend to use

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


# TODO we could maybe pass boolean needs_full_url instead of duplicating this function
def resolve_file_url_full(
    file_path: str,
    usage: FileUsage,
    request: HttpRequest | None = None,
) -> str:
    """Resolve a file path to its FULL URL ,including scheme and domain.

    Args:
        file_path: The file path to resolve
        usage: FileUsage type to determine which backend to use
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
