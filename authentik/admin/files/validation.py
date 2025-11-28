import re
from pathlib import PurePosixPath

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from authentik.admin.files.backends.passthrough import PassthroughBackend
from authentik.admin.files.backends.static import StaticBackend
from authentik.admin.files.usage import FileUsage

# File upload limits
MAX_FILE_NAME_LENGTH = 1024
MAX_PATH_COMPONENT_LENGTH = 255


def validate_file_name(name: str) -> None:
    if PassthroughBackend(FileUsage.MEDIA).supports_file(name) or StaticBackend(
        FileUsage.MEDIA
    ).supports_file(name):
        return
    validate_upload_file_name(name)


def validate_upload_file_name(
    name: str,
    ValidationError: type[Exception] = ValidationError,
) -> None:
    """Sanitize file path.

    Args:
        file_path: The file path to sanitize

    Returns:
        Sanitized file path

    Raises:
        ValidationError: If file path is invalid
    """
    if not name:
        raise ValidationError(_("File name cannot be empty"))

    # Allow alphanumeric, dots, hyphens, underscores, and forward slashes
    if not re.match(r"^[a-zA-Z0-9._/-]+$", name):
        raise ValidationError(
            _(
                "File name can only contain letters (a-z, A-Z), numbers (0-9), "
                "dots (.), hyphens (-), underscores (_), and forward slashes (/)"
            )
        )

    if "//" in name:
        raise ValidationError(_("File name cannot contain duplicate /"))

    # Convert to posix path
    path = PurePosixPath(name)

    # Check for absolute paths
    # Needs the / at the start. If it doesn't have it, it might still be unsafe, so see L53+
    if path.is_absolute():
        raise ValidationError(_("Absolute paths are not allowed"))

    # Check for parent directory references
    if ".." in path.parts:
        raise ValidationError(_("Parent directory references ('..') are not allowed"))

    # Disallow paths starting with dot (hidden files at root level)
    if str(path).startswith("."):
        raise ValidationError(_("Paths cannot start with '.'"))

    # Check path length limits
    normalized = str(path)
    if len(normalized) > MAX_FILE_NAME_LENGTH:
        raise ValidationError(_(f"File name too long (max {MAX_FILE_NAME_LENGTH} characters)"))

    for part in path.parts:
        if len(part) > MAX_PATH_COMPONENT_LENGTH:
            raise ValidationError(
                _(f"Path component too long (max {MAX_PATH_COMPONENT_LENGTH} characters)")
            )
