import re
from pathlib import PurePosixPath

from django.utils.translation import gettext as _
from rest_framework.exceptions import ValidationError

# File upload limits
MAX_FILE_SIZE_BYTES = 3 * 1024 * 1024  # 25MB
MAX_FILE_PATH_LENGTH = 1024
MAX_PATH_COMPONENT_LENGTH = 255

# Allowed MIME types per usage
ALLOWED_MIME_TYPES = {
    "media": ["image/"],
    "reports": None,
}


def sanitize_file_path(file_path: str) -> str:
    """Sanitize file path.

    Args:
        file_path: The file path to sanitize

    Returns:
        Sanitized file path

    Raises:
        ValidationError: If file path is invalid
    """
    if not file_path:
        raise ValidationError(_("File path cannot be empty"))

    # Strip whitespace
    file_path = file_path.strip()

    # Allow alphanumeric, dots, hyphens, underscores, and forward slashes
    if not re.match(r"^[a-zA-Z0-9._/-]+$", file_path):
        raise ValidationError(
            _(
                "Filename can only contain letters (a-z, A-Z), numbers (0-9), "
                "dots (.), hyphens (-), underscores (_), and forward slashes (/)"
            )
        )

    # Convert to posix path
    path = PurePosixPath(file_path)

    # Check for absolute paths
    # Needs the / at the start. If it doesn't have it, it might still be unsafe, so see L53+
    if path.is_absolute():
        raise ValidationError(_("Absolute paths are not allowed"))

    # Check for parent directory references
    if ".." in path.parts:
        raise ValidationError(_("Parent directory references (..) are not allowed"))

    # Disallow paths starting with dot (hidden files at root level)
    if str(path).startswith("."):
        raise ValidationError(_("Paths cannot start with '.'"))

    # Check path length limits
    normalized = str(path)
    if len(normalized) > MAX_FILE_PATH_LENGTH:
        raise ValidationError(_(f"File path too long (max {MAX_FILE_PATH_LENGTH} characters)"))

    for part in path.parts:
        if len(part) > MAX_PATH_COMPONENT_LENGTH:
            raise ValidationError(
                _(f"Path component too long (max {MAX_PATH_COMPONENT_LENGTH} characters)")
            )

    # Remove any duplicate slashes
    normalized = re.sub(r"/+", "/", normalized)

    return normalized


def validate_file_size(file_size: int, max_size: int = MAX_FILE_SIZE_BYTES) -> None:
    """Validate file size is within limits.

    Args:
        file_size: Size of file in bytes
        max_size: Maximum allowed size in bytes

    Raises:
        ValidationError: If file size exceeds max
    """
    if file_size > max_size:
        max_mb = max_size / 1024 / 1024
        actual_mb = file_size / 1024 / 1024
        raise ValidationError(
            {
                "file": [
                    _(
                        f"File size ({actual_mb:.2f}MB) exceeds maximum allowed "
                        f"size ({max_mb:.0f}MB)."
                    )
                ]
            }
        )


def validate_file_type(content_type: str, usage: str) -> None:
    """Validate file type is allowed for the given usage.

    Args:
        content_type: MIME type of the file
        usage: Usage type (e.g., "media", "reports")

    Raises:
        ValidationError: If file type is not allowed
    """
    allowed_types = ALLOWED_MIME_TYPES.get(usage)

    # None means no restrictions
    if allowed_types is None:
        return

    # Check if content_type starts with any allowed prefix
    content_type = content_type or ""
    for allowed_prefix in allowed_types:
        if content_type.startswith(allowed_prefix):
            return

    # If we get here, file type is not allowed
    expected = ", ".join(allowed_types)
    raise ValidationError(
        {
            "file": [
                _(
                    f"File type '{content_type}' not allowed for {usage} usage. "
                    f"Allowed types: {expected}"
                )
            ]
        }
    )
