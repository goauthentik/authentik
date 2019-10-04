"""passbook sentry integration"""
from structlog import get_logger

LOGGER = get_logger()


def before_send(event, hint):
    """Check if error is database error, and ignore if so"""
    from django_redis.exceptions import ConnectionInterrupted
    from django.db import OperationalError, InternalError
    from rest_framework.exceptions import APIException
    from billiard.exceptions import WorkerLostError
    from django.core.exceptions import DisallowedHost
    ignored_classes = (
        OperationalError,
        ConnectionInterrupted,
        APIException,
        InternalError,
        ConnectionResetError,
        WorkerLostError,
        DisallowedHost,
        ConnectionResetError,
    )
    if 'exc_info' in hint:
        _exc_type, exc_value, _ = hint['exc_info']
        if isinstance(exc_value, ignored_classes):
            LOGGER.info("Supressing error %r", exc_value)
            return None
    return event
