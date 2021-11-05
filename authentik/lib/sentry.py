"""authentik sentry integration"""
from typing import Optional

from aioredis.errors import ConnectionClosedError, ReplyError
from billiard.exceptions import SoftTimeLimitExceeded, WorkerLostError
from botocore.client import ClientError
from botocore.exceptions import BotoCoreError
from celery.exceptions import CeleryError
from channels.middleware import BaseMiddleware
from channels_redis.core import ChannelFull
from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation, ValidationError
from django.db import InternalError, OperationalError, ProgrammingError
from django.http.response import Http404
from django_redis.exceptions import ConnectionInterrupted
from docker.errors import DockerException
from h11 import LocalProtocolError
from ldap3.core.exceptions import LDAPException
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import RedisError, ResponseError
from rest_framework.exceptions import APIException
from sentry_sdk import Hub
from sentry_sdk.tracing import Transaction
from structlog.stdlib import get_logger
from websockets.exceptions import WebSocketException

from authentik.lib.utils.reflection import class_to_path

LOGGER = get_logger()


class SentryWSMiddleware(BaseMiddleware):
    """Sentry Websocket middleweare to set the transaction name based on
    consumer class path"""

    async def __call__(self, scope, receive, send):
        transaction: Optional[Transaction] = Hub.current.scope.transaction
        class_path = class_to_path(self.inner.consumer_class)
        if transaction:
            transaction.name = class_path
        return await self.inner(scope, receive, send)


class SentryIgnoredException(Exception):
    """Base Class for all errors that are suppressed, and not sent to sentry."""


def before_send(event: dict, hint: dict) -> Optional[dict]:
    """Check if error is database error, and ignore if so"""
    # pylint: disable=no-name-in-module
    from psycopg2.errors import Error

    ignored_classes = (
        # Inbuilt types
        KeyboardInterrupt,
        ConnectionResetError,
        OSError,
        PermissionError,
        # Django Errors
        Error,
        ImproperlyConfigured,
        OperationalError,
        InternalError,
        ProgrammingError,
        SuspiciousOperation,
        ValidationError,
        # Redis errors
        RedisConnectionError,
        ConnectionInterrupted,
        RedisError,
        ResponseError,
        ReplyError,
        ConnectionClosedError,
        # websocket errors
        ChannelFull,
        WebSocketException,
        LocalProtocolError,
        # rest_framework error
        APIException,
        # celery errors
        WorkerLostError,
        CeleryError,
        SoftTimeLimitExceeded,
        # S3 errors
        BotoCoreError,
        ClientError,
        # custom baseclass
        SentryIgnoredException,
        # ldap errors
        LDAPException,
        # Docker errors
        DockerException,
        # End-user errors
        Http404,
    )
    if "exc_info" in hint:
        _, exc_value, _ = hint["exc_info"]
        if isinstance(exc_value, ignored_classes):
            LOGGER.debug("dropping exception", exception=exc_value)
            return None
    if "logger" in event:
        if event["logger"] in [
            "dbbackup",
            "botocore",
            "kombu",
            "asyncio",
            "multiprocessing",
            "django_redis",
        ]:
            return None
    return event
