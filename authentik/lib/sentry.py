"""authentik sentry integration"""
from asyncio.exceptions import CancelledError
from typing import Any, Optional

from billiard.exceptions import SoftTimeLimitExceeded, WorkerLostError
from celery.exceptions import CeleryError
from channels_redis.core import ChannelFull
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation, ValidationError
from django.db import DatabaseError, InternalError, OperationalError, ProgrammingError
from django.http.response import Http404
from django_redis.exceptions import ConnectionInterrupted
from docker.errors import DockerException
from h11 import LocalProtocolError
from ldap3.core.exceptions import LDAPException
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import RedisError, ResponseError
from rest_framework.exceptions import APIException
from sentry_sdk import HttpTransport
from sentry_sdk import init as sentry_sdk_init
from sentry_sdk.api import set_tag
from sentry_sdk.integrations.argv import ArgvIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.socket import SocketIntegration
from sentry_sdk.integrations.stdlib import StdlibIntegration
from sentry_sdk.integrations.threading import ThreadingIntegration
from structlog.stdlib import get_logger
from websockets.exceptions import WebSocketException

from authentik import __version__, get_build_hash
from authentik.lib.config import CONFIG
from authentik.lib.utils.http import authentik_user_agent
from authentik.lib.utils.reflection import get_env

LOGGER = get_logger()


class SentryIgnoredException(Exception):
    """Base Class for all errors that are suppressed, and not sent to sentry."""


class SentryTransport(HttpTransport):
    """Custom sentry transport with custom user-agent"""

    def __init__(self, options: dict[str, Any]) -> None:
        super().__init__(options)
        self._auth = self.parsed_dsn.to_auth(authentik_user_agent())


def sentry_init(**sentry_init_kwargs):
    """Configure sentry SDK"""
    sentry_env = CONFIG.y("error_reporting.environment", "customer")
    kwargs = {
        "environment": sentry_env,
        "send_default_pii": CONFIG.y_bool("error_reporting.send_pii", False),
        "_experiments": {
            "profiles_sample_rate": float(CONFIG.y("error_reporting.sample_rate", 0.1)),
        },
    }
    kwargs.update(**sentry_init_kwargs)
    # pylint: disable=abstract-class-instantiated
    sentry_sdk_init(
        dsn=CONFIG.y("error_reporting.sentry_dsn"),
        integrations=[
            ArgvIntegration(),
            StdlibIntegration(),
            DjangoIntegration(transaction_style="function_name"),
            CeleryIntegration(monitor_beat_tasks=True),
            RedisIntegration(),
            ThreadingIntegration(propagate_hub=True),
            SocketIntegration(),
        ],
        before_send=before_send,
        traces_sampler=traces_sampler,
        release=f"authentik@{__version__}",
        transport=SentryTransport,
        **kwargs,
    )
    set_tag("authentik.build_hash", get_build_hash("tagged"))
    set_tag("authentik.env", get_env())
    set_tag("authentik.component", "backend")


def traces_sampler(sampling_context: dict) -> float:
    """Custom sampler to ignore certain routes"""
    path = sampling_context.get("asgi_scope", {}).get("path", "")
    _type = sampling_context.get("asgi_scope", {}).get("type", "")
    # Ignore all healthcheck routes
    if path.startswith("/-/health") or path.startswith("/-/metrics"):
        return 0
    if _type == "websocket":
        return 0
    return float(CONFIG.y("error_reporting.sample_rate", 0.1))


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
        DatabaseError,
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
        # AsyncIO
        CancelledError,
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
