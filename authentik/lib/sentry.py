"""authentik sentry integration"""
from typing import Optional

from aioredis.errors import ConnectionClosedError, ReplyError
from billiard.exceptions import SoftTimeLimitExceeded, WorkerLostError
from celery.exceptions import CeleryError
from channels.middleware import BaseMiddleware
from channels_redis.core import ChannelFull
from django.conf import settings
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
from sentry_sdk import init as sentry_sdk_init
from sentry_sdk.api import set_tag
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.threading import ThreadingIntegration
from sentry_sdk.tracing import Transaction
from structlog.stdlib import get_logger
from websockets.exceptions import WebSocketException

from authentik import __version__, get_build_hash
from authentik.lib.config import CONFIG
from authentik.lib.utils.reflection import class_to_path, get_env

LOGGER = get_logger()
SENTRY_DSN = "https://a579bb09306d4f8b8d8847c052d3a1d3@sentry.beryju.org/8"


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


def sentry_init(**sentry_init_kwargs):
    """Configure sentry SDK"""
    sentry_env = CONFIG.y("error_reporting.environment", "customer")
    kwargs = {
        "traces_sample_rate": float(CONFIG.y("error_reporting.sample_rate", 0.5)),
        "environment": sentry_env,
        "send_default_pii": CONFIG.y_bool("error_reporting.send_pii", False),
    }
    kwargs.update(**sentry_init_kwargs)
    # pylint: disable=abstract-class-instantiated
    sentry_sdk_init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(transaction_style="function_name"),
            CeleryIntegration(),
            RedisIntegration(),
            ThreadingIntegration(propagate_hub=True),
        ],
        before_send=before_send,
        release=f"authentik@{__version__}",
        **kwargs,
    )
    set_tag("authentik.build_hash", get_build_hash("tagged"))
    set_tag("authentik.env", get_env())
    set_tag("authentik.component", "backend")
    LOGGER.info(
        "Error reporting is enabled",
        env=kwargs["environment"],
    )


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
        # custom baseclass
        SentryIgnoredException,
        # ldap errors
        LDAPException,
        # Docker errors
        DockerException,
        # End-user errors
        Http404,
    )
    exc_value = None
    if "exc_info" in hint:
        _, exc_value, _ = hint["exc_info"]
        if isinstance(exc_value, ignored_classes):
            LOGGER.debug("dropping exception", exc=exc_value)
            return None
    if "logger" in event:
        if event["logger"] in [
            "kombu",
            "asyncio",
            "multiprocessing",
            "django_redis",
            "django.security.DisallowedHost",
            "django_redis.cache",
            "celery.backends.redis",
            "celery.worker",
            "paramiko.transport",
        ]:
            return None
    LOGGER.debug("sending event to sentry", exc=exc_value, source_logger=event.get("logger", None))
    if settings.DEBUG:
        return None
    return event
