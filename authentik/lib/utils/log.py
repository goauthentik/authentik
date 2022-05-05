"""Log utils"""
from contextlib import contextmanager
from typing import Optional

from structlog import BoundLogger
from structlog.stdlib import get_logger
from structlog.testing import capture_logs

LOGGER = get_logger()


@contextmanager
def capture_logs_tee(logger: Optional[BoundLogger] = None):
    """
    Capture logs using `capture_logs` but also output them.

    Warning: passed logger *must* be bound.
    """
    if not logger:
        logger = get_logger().bind()
    logs = []
    try:
        with capture_logs() as logs:
            yield logs
    finally:
        for log in logs:
            logger.msg(**log)
