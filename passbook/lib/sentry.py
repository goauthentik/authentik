"""passbook sentry integration"""
from billiard.exceptions import WorkerLostError
from botocore.client import ClientError
from django.core.exceptions import DisallowedHost, ValidationError
from django.db import InternalError, OperationalError, ProgrammingError
from django_redis.exceptions import ConnectionInterrupted
from redis.exceptions import RedisError
from rest_framework.exceptions import APIException
from structlog import get_logger

LOGGER = get_logger()


class SentryIgnoredException(Exception):
    """Base Class for all errors that are supressed, and not sent to sentry."""


def before_send(event, hint):
    """Check if error is database error, and ignore if so"""
    ignored_classes = (
        OperationalError,
        InternalError,
        ProgrammingError,
        ConnectionInterrupted,
        APIException,
        ConnectionResetError,
        WorkerLostError,
        DisallowedHost,
        ConnectionResetError,
        KeyboardInterrupt,
        ClientError,
        ValidationError,
        OSError,
        RedisError,
        SentryIgnoredException,
    )
    if "exc_info" in hint:
        _exc_type, exc_value, _ = hint["exc_info"]
        if isinstance(exc_value, ignored_classes):
            LOGGER.info("Supressing error %r", exc_value)
            return None
    return event
