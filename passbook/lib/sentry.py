"""passbook sentry integration"""
from billiard.exceptions import WorkerLostError
from botocore.client import ClientError
from celery.exceptions import CeleryError
from channels_redis.core import ChannelFull
from django.core.exceptions import DisallowedHost, ValidationError
from django.db import InternalError, OperationalError, ProgrammingError
from django_redis.exceptions import ConnectionInterrupted
from ldap3.core.exceptions import LDAPException
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import RedisError
from rest_framework.exceptions import APIException
from structlog import get_logger
from websockets.exceptions import WebSocketException

LOGGER = get_logger()


class SentryIgnoredException(Exception):
    """Base Class for all errors that are suppressed, and not sent to sentry."""


def before_send(event, hint):
    """Check if error is database error, and ignore if so"""
    ignored_classes = (
        OperationalError,
        InternalError,
        ProgrammingError,
        ConnectionInterrupted,
        APIException,
        ConnectionResetError,
        RedisConnectionError,
        WorkerLostError,
        DisallowedHost,
        ConnectionResetError,
        KeyboardInterrupt,
        ClientError,
        ValidationError,
        OSError,
        RedisError,
        SentryIgnoredException,
        CeleryError,
        LDAPException,
        ChannelFull,
        WebSocketException,
    )
    if "exc_info" in hint:
        _, exc_value, _ = hint["exc_info"]
        if isinstance(exc_value, ignored_classes):
            LOGGER.info("Supressing error %r", exc_value)
            return None
    return event
