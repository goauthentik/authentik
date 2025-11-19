"""error utils"""

from traceback import extract_tb
from typing import Any

from structlog.tracebacks import ExceptionDictTransformer

from authentik.lib.config import CONFIG
from authentik.lib.utils.reflection import class_to_path

TRACEBACK_HEADER = "Traceback (most recent call last):"
_exception_transformer = ExceptionDictTransformer(show_locals=CONFIG.get_bool("debug"))


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


def exception_to_dict(exc: Exception) -> list[dict[str, Any]]:
    """Format exception as a dictionary"""
    return _exception_transformer((type(exc), exc, exc.__traceback__))
