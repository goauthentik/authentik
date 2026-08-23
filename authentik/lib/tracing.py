"""authentik OpenTelemetry integration"""

from asyncio.exceptions import CancelledError
from contextlib import contextmanager
from typing import Any

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation, ValidationError
from django.db import DatabaseError, InternalError, OperationalError, ProgrammingError
from django.http.response import Http404
from docker.errors import DockerException
from dramatiq.errors import Retry
from h11 import LocalProtocolError
from ldap3.core.exceptions import LDAPException
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware
from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.structlog import StructlogInstrumentor
from opentelemetry.instrumentation.threading import ThreadingInstrumentor
from opentelemetry.propagate import inject
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased
from opentelemetry.trace import Span as OtelSpan
from opentelemetry.trace import Status, StatusCode
from psycopg.errors import Error
from rest_framework.exceptions import APIException
from structlog.stdlib import get_logger
from websockets.exceptions import WebSocketException

from authentik import authentik_build_hash, authentik_version
from authentik.lib.config import CONFIG
from authentik.lib.utils.reflection import get_env

LOGGER = get_logger()
_root_path = CONFIG.get("web.path", "/")

tracer = trace.get_tracer("authentik")

# Set by lifecycle/gunicorn.conf.py before the app is preloaded, to tell
# AuthentikCoreConfig.ready() to skip otel_init_provider() (see its docstring)
OTEL_DEFER_PROVIDER_ENV_VAR = "AUTHENTIK_OTEL_DEFER_PROVIDER"


class TracingIgnoredException(Exception):
    """Base Class for all errors that are suppressed, and not recorded as span errors."""


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
    # websocket errors
    WebSocketException,
    LocalProtocolError,
    # rest_framework error
    APIException,
    # dramatiq errors
    Retry,
    # custom baseclass
    TracingIgnoredException,
    # ldap errors
    LDAPException,
    # Docker errors
    DockerException,
    # End-user errors
    Http404,
    # AsyncIO
    CancelledError,
)


def _build_span_exporter() -> OTLPSpanExporter:
    # error_reporting.otel_endpoint is the base OTLP endpoint (matching the standard
    # OTEL_EXPORTER_OTLP_ENDPOINT convention), so the per-signal path must be appended here;
    # unlike OTEL_EXPORTER_OTLP_ENDPOINT, passing `endpoint=` directly skips that step
    endpoint = CONFIG.get("error_reporting.otel_endpoint")
    if not endpoint:
        return OTLPSpanExporter()
    return OTLPSpanExporter(endpoint=f"{endpoint.rstrip('/')}/v1/traces")


def otel_instrument():
    """Wire up automatic instrumentation (requests, threading, structlog, psycopg queries).
    Safe to call before a fork: this only patches library internals and captures a lazy
    proxy tracer that resolves once a real TracerProvider is set later by
    otel_init_provider(). Django's own request/response spans come from wrapping the ASGI
    app instead (see otel_wrap_asgi): opentelemetry-instrumentation-django's middleware
    only supports Django's WSGI path, and authentik is served entirely over ASGI"""
    ThreadingInstrumentor().instrument()
    RequestsInstrumentor().instrument()
    StructlogInstrumentor().instrument()
    PsycopgInstrumentor().instrument()


def otel_wrap_asgi(app):
    """Wrap an ASGI application to create a span per request.
    Call this on the app returned by django.core.asgi.get_asgi_application(), after
    otel_init_provider() has set the real TracerProvider (see authentik/root/asgi.py)"""
    return OpenTelemetryMiddleware(
        app,
        excluded_urls=f"{_root_path}-/health,{_root_path}-/metrics",
        exclude_spans=["receive", "send"],
    )


def otel_init_provider():
    """Create and set the real OpenTelemetry TracerProvider and span exporter.

    Must run after any fork that will happen: BatchSpanProcessor starts a background
    export thread, and if a lock it holds is inherited mid-fork, the child can deadlock
    on it forever (see
    https://opentelemetry-python.readthedocs.io/en/latest/examples/fork-process-model/).
    Under gunicorn's preload_app, call otel_instrument() from AuthentikCoreConfig.ready()
    (before the fork) and this function from a post_fork hook (after the fork) instead"""
    sample_rate = 1 if settings.DEBUG else float(CONFIG.get("error_reporting.sample_rate", 0.1))
    provider = TracerProvider(
        resource=Resource.create(
            {
                "service.name": "authentik-v2",
                "service.version": authentik_version(),
                "deployment.environment": CONFIG.get("error_reporting.environment", "customer"),
                "authentik.build_hash": authentik_build_hash("tagged"),
                "authentik.env": get_env(),
                "authentik.component": "backend",
            }
        ),
        sampler=ParentBased(TraceIdRatioBased(sample_rate)),
    )
    provider.add_span_processor(SimpleSpanProcessor(_build_span_exporter()))
    trace.set_tracer_provider(provider)
    LOGGER.info("Enabled Open Telemetry tracing")


def otel_init():
    """Full init for single-process entrypoints that never fork afterwards (management
    commands, the test runner, dramatiq workers). For gunicorn's preloaded web server,
    call otel_instrument() and otel_init_provider() separately instead, see their docs"""
    otel_instrument()
    otel_init_provider()


def should_ignore_exception(exc: Exception) -> bool:
    """Check if an exception should be dropped"""
    return isinstance(exc, ignored_classes)


def record_exception(exc: Exception):
    """Record an exception on the current span"""
    span = trace.get_current_span()
    span.record_exception(exc)
    span.set_status(Status(StatusCode.ERROR))


def set_tag(key: str, value: Any):
    """Set an attribute on the current span"""
    trace.get_current_span().set_attribute(key, str(value))


class Span:
    """Thin wrapper around an OpenTelemetry span exposing a sentry_sdk-like API"""

    def __init__(self, span: OtelSpan):
        self._span = span
        self._description: str | None = None

    def set_data(self, key: str, value: Any):
        """Set an attribute on the wrapped span"""
        self._span.set_attribute(key, str(value))

    @property
    def description(self) -> str | None:
        return self._description

    @description.setter
    def description(self, value: str):
        self._description = value
        self._span.set_attribute("description", str(value))


@contextmanager
def start_span(op: str, name: str | None = None):
    """Start a new span, compatible with the previous sentry_sdk.start_span API"""
    with tracer.start_as_current_span(op, attributes={"name": name}) as span:
        yield Span(span)


def get_http_meta() -> dict[str, str]:
    """Get trace-context propagation headers for the current span"""
    carrier: dict[str, str] = {}
    inject(carrier)
    return carrier
