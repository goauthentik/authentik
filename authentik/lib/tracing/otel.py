"""authentik OpenTelemetry integration"""

import sys
from contextlib import contextmanager
from inspect import iscoroutinefunction
from platform import machine
from socket import gethostname
from typing import Any

from asgiref.sync import markcoroutinefunction
from django.conf import settings
from django.utils.module_loading import import_string
from opentelemetry import trace
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.structlog import StructlogInstrumentor
from opentelemetry.instrumentation.threading import ThreadingInstrumentor
from opentelemetry.propagate import inject, set_global_textmap
from opentelemetry.propagators.b3 import B3MultiFormat
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.sdk.resources import HOST_ARCH, HOST_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased
from opentelemetry.trace import Span as OtelSpan
from opentelemetry.trace import Status, StatusCode
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from structlog.stdlib import get_logger

from authentik import authentik_build_hash, authentik_version
from authentik.lib.config import CONFIG
from authentik.lib.tracing.common import Tracer
from authentik.lib.utils.reflection import get_env

LOGGER = get_logger()
_root_path = CONFIG.get("web.path", "/")

tracer = trace.get_tracer("authentik")


def _trace_middleware_list(middleware_paths: list[str]) -> list[str]:
    """Wrap each MIDDLEWARE entry so it gets a span named after its dotted path.
    Must run before Django builds the handler from the final MIDDLEWARE list."""
    return [_traced_middleware_path(path) for path in middleware_paths]


def _traced_middleware_path(path: str) -> str:
    """Build a wrapper class for `path` and register it on this module, so Django's
    import_string() can resolve the dotted path this returns back to it"""
    real_middleware = import_string(path)

    class _TracedMiddleware:
        # Mirror the real middleware's declared capabilities so Django's load_middleware()
        # adapts the handler passed to our __init__ exactly as it would for the real one
        sync_capable = getattr(real_middleware, "sync_capable", True)
        async_capable = getattr(real_middleware, "async_capable", False)

        def __init__(self, get_response):
            self.inner = real_middleware(get_response)
            if iscoroutinefunction(self.inner):
                markcoroutinefunction(self)
            for hook in ("process_view", "process_exception", "process_template_response"):
                if hasattr(self.inner, hook):
                    setattr(self, hook, getattr(self.inner, hook))

        def __call__(self, request):
            if iscoroutinefunction(self):
                return self.__acall__(request)
            with tracer.start_as_current_span(path):
                return self.inner(request)

        async def __acall__(self, request):
            with tracer.start_as_current_span(path):
                return await self.inner(request)

    attr_name = "_traced_" + path.replace(".", "_")
    setattr(sys.modules[__name__], attr_name, _TracedMiddleware)
    return f"{__name__}.{attr_name}"


class _Span:
    """Thin wrapper around an OpenTelemetry span exposing a sentry_sdk-like API"""

    def __init__(self, span: OtelSpan):
        self._span = span
        self._description: str | None = None

    def set_data(self, key: str, value: Any) -> None:
        self._span.set_attribute(key, str(value))

    @property
    def description(self) -> str | None:
        return self._description

    @description.setter
    def description(self, value: str) -> None:
        self._description = value
        self._span.set_attribute("description", str(value))


class OpenTelemetryTracer(Tracer):
    """Tracer backed by OpenTelemetry, exporting spans over OTLP to
    error_reporting.otel_endpoint"""

    def setup_pre_fork(self) -> None:
        """Wire up automatic instrumentation and per-middleware spans. Safe to call
        before a fork; must run after Django settings have fully loaded, since
        DjangoInstrumentor patches MIDDLEWARE.

        Needs opentelemetry-instrumentation-asgi installed (never imported directly
        here), or DjangoInstrumentor silently falls back to WSGI-only, which authentik
        never uses."""
        # Must run before instrument() below, so DjangoInstrumentor's own middleware is
        # inserted afterwards and doesn't get wrapped a second time
        settings.MIDDLEWARE = _trace_middleware_list(settings.MIDDLEWARE)
        set_global_textmap(
            CompositePropagator(
                [TraceContextTextMapPropagator(), W3CBaggagePropagator(), B3MultiFormat()]
            )
        )
        ThreadingInstrumentor().instrument()
        RequestsInstrumentor().instrument()
        StructlogInstrumentor().instrument()
        PsycopgInstrumentor().instrument()
        DjangoInstrumentor().instrument(
            excluded_urls=f"{_root_path}-/health,{_root_path}-/metrics",
            is_sql_commentor_enabled=True,
        )

    def setup_post_fork(self) -> None:
        """Create and set the real OpenTelemetry TracerProvider and span exporter.

        Must run after any fork: BatchSpanProcessor's background export thread doesn't
        survive fork() safely. Under gunicorn's preload_app, call this from a post_fork
        hook, after setup_pre_fork() has run pre-fork."""
        sample_rate = 1 if settings.DEBUG else float(CONFIG.get("error_reporting.sample_rate", 0.1))
        provider = TracerProvider(
            resource=Resource.create(
                {
                    "service.name": "authentik",
                    "service.version": authentik_version(),
                    "deployment.environment": CONFIG.get("error_reporting.environment", "customer"),
                    "authentik.build_hash": authentik_build_hash("tagged"),
                    "authentik.env": get_env(),
                    "authentik.component": "backend",
                    HOST_NAME: gethostname(),
                    HOST_ARCH: machine(),
                }
            ),
            sampler=ParentBased(TraceIdRatioBased(sample_rate)),
        )
        # error_reporting.otel_endpoint is the base OTLP endpoint (matching the standard
        # OTEL_EXPORTER_OTLP_ENDPOINT convention), so the per-signal path must be appended here;
        # unlike OTEL_EXPORTER_OTLP_ENDPOINT, passing `endpoint=` directly skips that step
        endpoint = CONFIG.get("error_reporting.otel_endpoint")
        exporter = (
            OTLPSpanExporter(endpoint=f"{endpoint.rstrip('/')}/v1/traces")
            if endpoint
            else OTLPSpanExporter()
        )
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        LOGGER.info("Enabled Open Telemetry tracing")

    def record_exception(self, exc: Exception) -> None:
        span = trace.get_current_span()
        span.record_exception(exc)
        span.set_status(Status(StatusCode.ERROR))

    def get_http_meta(self) -> dict[str, str]:
        carrier: dict[str, str] = {}
        inject(carrier)
        return carrier

    def set_tag(self, key: str, value: Any) -> None:
        trace.get_current_span().set_attribute(key, str(value))

    @contextmanager
    def start_span(self, op: str, name: str | None = None):
        with tracer.start_as_current_span(op, attributes={"name": name or op}) as span:
            yield _Span(span)
