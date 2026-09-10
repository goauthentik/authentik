"""test OpenTelemetry integration"""

from unittest.mock import patch

from asgiref.sync import async_to_sync
from django.test import TestCase
from django.utils.module_loading import import_string
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from authentik.lib.tracing import otel_django_middleware
from authentik.lib.tracing.exceptions import TracingIgnoredException, should_ignore_exception
from authentik.lib.tracing.otel_django_middleware import _traced_middleware_path


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


class DummyMiddleware:
    """Sync middleware doing work before and after get_response, for phase tracing tests"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _marker("dummy_pre")
        response = self.get_response(request)
        _marker("dummy_post")
        return response


class DummyAsyncMiddleware:
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
    """test per-middleware phase spans"""

    def setUp(self):
        self.exporter = InMemorySpanExporter()
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(self.exporter))
        patcher = patch.object(otel_django_middleware, "tracer", provider.get_tracer(__name__))
        patcher.start()
        self.addCleanup(patcher.stop)

    def _run(self, path, get_response):
        middleware = import_string(_traced_middleware_path(path))(get_response)
        result = middleware("request")
        return middleware, result

    def _assert_phases(self, path):
        spans = {span.name: span for span in self.exporter.get_finished_spans()}
        self.assertEqual(
            [span.name for span in self.exporter.get_finished_spans()],
            ["dummy_pre", f"{path} (pre)", "handler", "dummy_post", f"{path} (post)"],
        )
        # Each phase only covers the middleware's own work, not the handler's
        self.assertLessEqual(spans[f"{path} (pre)"].end_time, spans["handler"].start_time)
        self.assertGreaterEqual(spans[f"{path} (post)"].start_time, spans["handler"].end_time)
        # The middleware's own work is nested in the matching phase
        self.assertEqual(spans["dummy_pre"].parent.span_id, spans[f"{path} (pre)"].context.span_id)
        self.assertEqual(
            spans["dummy_post"].parent.span_id, spans[f"{path} (post)"].context.span_id
        )
        # ...and the handler is not nested in either phase, since the pre phase is closed
        # before the middleware chain descends
        handler_parent = spans["handler"].parent
        self.assertNotIn(
            handler_parent.span_id if handler_parent else None,
            {spans[f"{path} (pre)"].context.span_id, spans[f"{path} (post)"].context.span_id},
        )

    def test_phases_sync(self):
        """Test pre and post processing are timed separately"""
        path = "authentik.lib.tests.test_otel.DummyMiddleware"

        def get_response(request):
            _marker("handler")
            return "response"

        _, result = self._run(path, get_response)
        self.assertEqual(result, "response")
        self._assert_phases(path)

    def test_phases_async(self):
        """Test pre and post processing are timed separately for async middleware"""
        path = "authentik.lib.tests.test_otel.DummyAsyncMiddleware"

        async def get_response(request):
            _marker("handler")
            return "response"

        middleware = import_string(_traced_middleware_path(path))(get_response)
        self.assertEqual(async_to_sync(middleware)("request"), "response")
        self._assert_phases(path)

    def test_phase_short_circuit(self):
        """Test a middleware that never calls get_response only gets a pre span"""

        class ShortCircuit:
            def __init__(self, get_response):
                self.get_response = get_response

            def __call__(self, request):
                return "short"

        path = "authentik.lib.tests.test_otel.DummyMiddleware"
        with patch("authentik.lib.tests.test_otel.DummyMiddleware", ShortCircuit):
            middleware = import_string(_traced_middleware_path(path))(lambda request: "response")
        self.assertEqual(middleware("request"), "short")
        self.assertEqual(
            [span.name for span in self.exporter.get_finished_spans()], [f"{path} (pre)"]
        )
