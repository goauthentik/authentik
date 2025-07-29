"""authentik sentry integration"""

from asyncio.exceptions import CancelledError
from typing import Any

from channels_redis.core import ChannelFull
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation, ValidationError
from django.db import DatabaseError, InternalError, OperationalError, ProgrammingError
from django.http.response import Http404
from django_redis.exceptions import ConnectionInterrupted
from docker.errors import DockerException
from h11 import LocalProtocolError
from ldap3.core.exceptions import LDAPException
from psycopg.errors import Error
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import RedisError, ResponseError
from rest_framework.exceptions import APIException
from sentry_sdk import HttpTransport, get_current_scope
from sentry_sdk import init as sentry_sdk_init
from sentry_sdk.api import set_tag
from sentry_sdk.integrations.argv import ArgvIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.socket import SocketIntegration
from sentry_sdk.integrations.stdlib import StdlibIntegration
from sentry_sdk.integrations.threading import ThreadingIntegration
from sentry_sdk.tracing import BAGGAGE_HEADER_NAME, SENTRY_TRACE_HEADER_NAME
from structlog.stdlib import get_logger
from websockets.exceptions import WebSocketException

from authentik import __version__, get_build_hash
from authentik.lib.config import CONFIG
from authentik.lib.utils.http import authentik_user_agent
from authentik.lib.utils.reflection import get_env

LOGGER = get_logger()
_root_path = CONFIG.get("web.path", "/")


class SentryIgnoredException(Exception):
    """Base Class for all errors that are suppressed, and not sent to sentry."""


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


class SentryTransport(HttpTransport):
    """Custom sentry transport with custom user-agent"""

    def __init__(self, options: dict[str, Any]) -> None:
        super().__init__(options)
        self._auth = self.parsed_dsn.to_auth(authentik_user_agent())


def sentry_init(**sentry_init_kwargs):
    """Configure sentry SDK"""
    sentry_env = CONFIG.get("error_reporting.environment", "customer")
    kwargs = {
        "environment": sentry_env,
        "send_default_pii": CONFIG.get_bool("error_reporting.send_pii", False),
        "_experiments": {
            "profiles_sample_rate": float(CONFIG.get("error_reporting.sample_rate", 0.1)),
        },
        **sentry_init_kwargs,
        **CONFIG.get_dict_from_b64_json("error_reporting.extra_args", {}),
    }

    sentry_sdk_init(
        dsn=CONFIG.get("error_reporting.sentry_dsn"),
        integrations=[
            ArgvIntegration(),
            StdlibIntegration(),
            DjangoIntegration(transaction_style="function_name", cache_spans=True),
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
    if path.startswith(f"{_root_path}-/health") or path.startswith(f"{_root_path}-/metrics"):
        return 0
    if _type == "websocket":
        return 0
    if CONFIG.get_bool("debug"):
        return 1
    return float(CONFIG.get("error_reporting.sample_rate", 0.1))


def should_ignore_exception(exc: Exception) -> bool:
    """Check if an exception should be dropped"""
    return isinstance(exc, ignored_classes)


def before_send(event: dict, hint: dict) -> dict | None:
    """Check if error is database error, and ignore if so"""
    exc_value = None
    if "exc_info" in hint:
        _, exc_value, _ = hint["exc_info"]
        if should_ignore_exception(exc_value):
            LOGGER.debug("dropping exception", exc=exc_value)
            return None
    if "logger" in event:
        if event["logger"] in [
            "asyncio",
            "multiprocessing",
            "django_redis",
            "django.security.DisallowedHost",
            "django_redis.cache",
            "paramiko.transport",
        ]:
            return None
    LOGGER.debug("sending event to sentry", exc=exc_value, source_logger=event.get("logger", None))
    if settings.DEBUG:
        return None
    return event


def get_http_meta():
    """Get sentry-related meta key-values"""
    scope = get_current_scope()
    meta = {
        SENTRY_TRACE_HEADER_NAME: scope.get_traceparent() or "",
    }
    if bag := scope.get_baggage():
        meta[BAGGAGE_HEADER_NAME] = bag.serialize()
    return meta
