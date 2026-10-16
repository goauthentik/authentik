"""test OpenTelemetry integration"""

from unittest.mock import patch

from asgiref.sync import async_to_sync
from django.test import TestCase
from django.utils.deprecation import MiddlewareMixin
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from authentik.lib.tracing import otel_django_middleware
from authentik.lib.tracing.exceptions import TracingIgnoredException, should_ignore_exception
from authentik.lib.tracing.otel_django_middleware import TracedMiddleware


def _marker(name: str) -> None:
    """Emit a span from the tracer the middleware wrapper uses, so tests can patch it"""
    otel_django_middleware.tracer.start_span(name).end()


class TestOtel(TestCase):
    """test OpenTelemetry integration"""

    def test_error_not_sent(self):
        """Test TracingIgnoredException not recorded"""
        self.assertTrue(should_ignore_exception(TracingIgnoredException()))

    def test_error_sent(self):
        """Test error recorded"""
        self.assertFalse(should_ignore_exception(ValueError()))


class DummyMiddleware(TracedMiddleware):
    """Sync middleware doing work before and after get_response, for tracing tests"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _marker("dummy_pre")
        response = self.get_response(request)
        _marker("dummy_post")
        return response


class DummyAsyncMiddleware(TracedMiddleware):
    """Async equivalent of DummyMiddleware"""

    sync_capable = False
    async_capable = True

    def __init__(self, get_response):
        self.get_response = get_response

    async def __call__(self, request):
        _marker("dummy_pre")
        response = await self.get_response(request)
        _marker("dummy_post")
        return response


class TestOtelMiddleware(TestCase):
    """test per-middleware spans"""

    def setUp(self):
        self.exporter = InMemorySpanExporter()
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(self.exporter))
        patcher = patch.object(otel_django_middleware, "tracer", provider.get_tracer(__name__))
        patcher.start()
        self.addCleanup(patcher.stop)

    def _assert_span(self, path):
        spans = {span.name: span for span in self.exporter.get_finished_spans()}
        self.assertEqual(
            [span.name for span in self.exporter.get_finished_spans()],
            ["dummy_pre", "handler", "dummy_post", path],
        )
        # The middleware's own work and everything it calls are nested in its span
        for name in ("dummy_pre", "handler", "dummy_post"):
            self.assertEqual(spans[name].parent.span_id, spans[path].context.span_id)

    def test_span_sync(self):
        """Test sync middleware is traced"""

        def get_response(request):
            _marker("handler")
            return "response"

        self.assertEqual(DummyMiddleware(get_response)("request"), "response")
        self._assert_span("authentik.lib.tests.test_otel.DummyMiddleware")

    def test_span_async(self):
        """Test async middleware is traced"""

        async def get_response(request):
            _marker("handler")
            return "response"

        middleware = DummyAsyncMiddleware(get_response)
        self.assertEqual(async_to_sync(middleware)("request"), "response")
        self._assert_span("authentik.lib.tests.test_otel.DummyAsyncMiddleware")

    def test_span_mixin(self):
        """Test MiddlewareMixin subclasses are traced, sync and async"""

        class Mixin(TracedMiddleware, MiddlewareMixin):
            def process_request(self, request):
                _marker("dummy_pre")

            def process_response(self, request, response):
                _marker("dummy_post")
                return response

        def get_response(request):
            _marker("handler")
            return "response"

        async def aget_response(request):
            return get_response(request)

        path = f"{__name__}.{Mixin.__qualname__}"
        self.assertEqual(Mixin(get_response)("request"), "response")
        self._assert_span(path)
        self.exporter.clear()
        self.assertEqual(async_to_sync(Mixin(aget_response))("request"), "response")
        self._assert_span(path)

    def test_untraced(self):
        """Test middleware not inheriting TracedMiddleware isn't traced"""

        class Plain:
            def __init__(self, get_response):
                self.get_response = get_response

            def __call__(self, request):
                return self.get_response(request)

        self.assertEqual(Plain(lambda request: "response")("request"), "response")
        self.assertEqual(self.exporter.get_finished_spans(), ())
