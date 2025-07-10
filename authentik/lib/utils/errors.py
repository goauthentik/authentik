"""error utils"""

from traceback import extract_tb

from structlog.tracebacks import ExceptionDictTransformer

from authentik.lib.utils.reflection import class_to_path

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


def exception_to_dict(exc: Exception) -> dict:
    """Format exception as a dictionary"""
    return ExceptionDictTransformer()((type(exc), exc, exc.__traceback__))
