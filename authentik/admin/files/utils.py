"""Utility functions for file handling"""

import mimetypes


def get_mime_from_filename(filename: str) -> str:
    """Get MIME type from filename.

    Args:
        filename: Name of the file

    Returns:
        MIME type string
    """
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"
