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
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.structlog import StructlogInstrumentor
from opentelemetry.instrumentation.threading import ThreadingInstrumentor
from opentelemetry.propagate import inject
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
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
from authentik.root.install_id import get_install_id

LOGGER = get_logger()
_root_path = CONFIG.get("web.path", "/")

tracer = trace.get_tracer("authentik")


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


def otel_init():
    """Configure the global OpenTelemetry TracerProvider.
    Must run after Django settings have fully loaded, since DjangoInstrumentor inserts
    its own middleware into django.conf.settings.MIDDLEWARE (see AuthentikCoreConfig.ready).

    Under gunicorn's preload_app, this runs once in the master before workers are forked; call
    otel_reinit_exporter() from a post_fork hook to give each worker a live export thread"""
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
                "authentik.uuid": get_install_id(),
            }
        ),
        sampler=ParentBased(TraceIdRatioBased(sample_rate)),
    )
    provider.add_span_processor(BatchSpanProcessor(_build_span_exporter()))
    trace.set_tracer_provider(provider)
    ThreadingInstrumentor().instrument()
    RequestsInstrumentor().instrument()
    StructlogInstrumentor().instrument()
    DjangoInstrumentor().instrument(
        excluded_urls=f"{_root_path}-/health,{_root_path}-/metrics",
        is_sql_commentor_enabled=True,
    )
    LOGGER.info("Enabled Open Telemetry tracing")


def otel_reinit_exporter():
    """Re-attach a fresh span exporter after a process fork."""
    provider = trace.get_tracer_provider()
    if not isinstance(provider, TracerProvider):
        LOGGER.warn("no provider")
        return
    provider.add_span_processor(BatchSpanProcessor(_build_span_exporter()))


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
