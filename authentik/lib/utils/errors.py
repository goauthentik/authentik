"""error utils"""
from traceback import format_tb

TRACEBACK_HEADER = "Traceback (most recent call last):\n"


def exception_to_string(exc: Exception) -> str:
    """Convert exception to string stackrace"""
    # Either use passed original exception or whatever we have
    return TRACEBACK_HEADER + "".join(format_tb(exc.__traceback__)) + str(exc)
