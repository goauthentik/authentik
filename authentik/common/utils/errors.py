"""error utils"""

from traceback import extract_tb

from authentik.common.utils.reflection import class_to_path

TRACEBACK_HEADER = "Traceback (most recent call last):"


def exception_to_string(exc: Exception) -> str:
    """Convert exception to string stackrace"""
    # Either use passed original exception or whatever we have
    return "\n".join(
        [
            TRACEBACK_HEADER,
            *[x.rstrip() for x in extract_tb(exc.__traceback__).format()],
            f"{class_to_path(exc.__class__)}: {str(exc)}",
        ]
    )
