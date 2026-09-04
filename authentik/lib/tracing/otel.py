"""authentik OpenTelemetry integration"""

import sys
from contextlib import contextmanager
from typing import Any

from asgiref.sync import iscoroutinefunction, markcoroutinefunction
from django.conf import settings
from django.utils.module_loading import import_string
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.django import DjangoInstrumentor
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
from structlog.stdlib import get_logger

from authentik import authentik_build_hash, authentik_version
from authentik.lib.config import CONFIG
from authentik.lib.utils.reflection import get_env

LOGGER = get_logger()
_root_path = CONFIG.get("web.path", "/")

tracer = trace.get_tracer("authentik")

# Set by lifecycle/gunicorn.conf.py before the app is preloaded, to tell
# AuthentikCoreConfig.ready() to skip otel_init_provider() (see its docstring)
OTEL_DEFER_PROVIDER_ENV_VAR = "AUTHENTIK_OTEL_DEFER_PROVIDER"


def otel_instrument():
    """Wire up automatic instrumentation. Safe to call before a fork; must run after
    Django settings have fully loaded, since DjangoInstrumentor patches MIDDLEWARE.

    Needs opentelemetry-instrumentation-asgi installed (never imported directly here),
    or DjangoInstrumentor silently falls back to WSGI-only, which authentik never uses."""
    ThreadingInstrumentor().instrument()
    RequestsInstrumentor().instrument()
    StructlogInstrumentor().instrument()
    PsycopgInstrumentor().instrument()
    DjangoInstrumentor().instrument(
        excluded_urls=f"{_root_path}-/health,{_root_path}-/metrics",
        is_sql_commentor_enabled=True,
    )


def trace_middleware_list(middleware_paths: list[str]) -> list[str]:
    """Wrap each MIDDLEWARE entry so it gets a span named after its dotted path.
    Call on the final assembled MIDDLEWARE list, before Django builds the handler."""
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


def otel_init_provider():
    """Create and set the real OpenTelemetry TracerProvider and span exporter.

    Must run after any fork: BatchSpanProcessor's background export thread doesn't
    survive fork() safely. Under gunicorn's preload_app, call this from a post_fork
    hook, after otel_instrument() has run pre-fork."""
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


def otel_init():
    """Full init for single-process entrypoints that never fork afterwards. Gunicorn's
    preloaded web server calls otel_instrument()/otel_init_provider() separately instead"""
    otel_instrument()
    otel_init_provider()


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
