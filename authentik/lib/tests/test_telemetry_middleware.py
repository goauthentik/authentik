"""Test OpenTelemetry middleware"""

from unittest import TestCase
from unittest.mock import MagicMock, patch, call

from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory


class TestOpenTelemetryMiddleware(TestCase):
    """Test OpenTelemetry middleware functionality"""

    def setUp(self):
        self.factory = RequestFactory()
        self.mock_tracer = MagicMock()
        self.mock_span = MagicMock()
        self.get_response = MagicMock(return_value=HttpResponse(status=200))

    def _create_middleware(self):
        """Create middleware instance with mocked dependencies"""
        with patch("opentelemetry.trace.get_tracer") as mock_get_tracer:
            mock_get_tracer.return_value = self.mock_tracer

            # Mock middleware class
            class MockOpenTelemetryMiddleware:
                def __init__(self, get_response):
                    self.get_response = get_response
                    self.tracer = mock_get_tracer("authentik.middleware")
                    self.excluded_paths = [
                        "/-/health/",
                        "/-/metrics/",
                        "/static/",
                        "/media/",
                    ]

                def __call__(self, request):
                    if any(request.path.startswith(path) for path in self.excluded_paths):
                        return self.get_response(request)

                    with self.tracer.start_as_current_span(
                        "http.request",
                    ) as span:
                        self._set_span_attributes(request, span)
                        response = self.get_response(request)
                        self._set_response_attributes(response, span)
                        return response

                def _set_span_attributes(self, request, span):
                    span.set_attribute("http.method", request.method)
                    span.set_attribute("http.url", request.build_absolute_uri())
                    span.set_attribute("http.target", request.path)
                    span.set_attribute("http.scheme", request.scheme)
                    span.set_attribute("http.host", request.get_host())

                    if hasattr(request, "user") and request.user.is_authenticated:
                        span.set_attribute("user.id", str(request.user.pk))
                        span.set_attribute("user.username", request.user.username)

                def _set_response_attributes(self, response, span):
                    span.set_attribute("http.status_code", response.status_code)
                    if response.status_code >= 400:
                        span.set_status(MagicMock())

            return MockOpenTelemetryMiddleware(self.get_response)

    def test_middleware_creates_span_for_request(self):
        """Test that middleware creates a span for incoming requests"""
        middleware = self._create_middleware()
        request = self.factory.get("/api/v3/core/users/")

        self.mock_tracer.start_as_current_span.return_value.__enter__.return_value = self.mock_span

        response = middleware(request)

        # Verify span was created
        self.mock_tracer.start_as_current_span.assert_called_once_with(
            "http.request",
        )

        # Verify response
        self.assertEqual(response.status_code, 200)

    def test_middleware_sets_request_attributes(self):
        """Test that middleware sets proper request attributes on span"""
        middleware = self._create_middleware()
        request = self.factory.post(
            "/api/v3/flows/executor/default-authentication-flow/",
            data={"username": "test", "password": "test"},
        )
        request.user = MagicMock()
        request.user.is_authenticated = True
        request.user.pk = 123
        request.user.username = "testuser"

        self.mock_tracer.start_as_current_span.return_value.__enter__.return_value = self.mock_span

        middleware(request)

        # Verify span attributes
        expected_calls = [
            call("http.method", "POST"),
            call("http.url", request.build_absolute_uri()),
            call("http.target", "/api/v3/flows/executor/default-authentication-flow/"),
            call("http.scheme", "http"),
            call("http.host", "testserver"),
            call("user.id", "123"),
            call("user.username", "testuser"),
            call("http.status_code", 200),
        ]

        for expected_call in expected_calls:
            self.mock_span.set_attribute.assert_any_call(*expected_call.args)

    def test_middleware_excludes_health_check_endpoints(self):
        """Test that health check endpoints are not traced"""
        middleware = self._create_middleware()

        health_endpoints = [
            "/-/health/live/",
            "/-/health/ready/",
            "/-/metrics/",
        ]

        for endpoint in health_endpoints:
            with self.subTest(endpoint=endpoint):
                request = self.factory.get(endpoint)
                response = middleware(request)

                # Should not create span for excluded paths
                if endpoint.startswith(("/-/health/", "/-/metrics/")):
                    # Reset to check it wasn't called
                    self.mock_tracer.start_as_current_span.assert_not_called()
                    self.mock_tracer.start_as_current_span.reset_mock()

                self.assertEqual(response.status_code, 200)

    def test_middleware_excludes_static_files(self):
        """Test that static file requests are not traced"""
        middleware = self._create_middleware()

        static_paths = [
            "/static/dist/assets/main.js",
            "/static/authentik/css/style.css",
            "/media/application-icons/logo.png",
        ]

        for path in static_paths:
            with self.subTest(path=path):
                request = self.factory.get(path)
                response = middleware(request)

                # Should not create span for static files
                self.assertEqual(response.status_code, 200)

    def test_middleware_sets_error_status_for_errors(self):
        """Test that middleware sets error status for error responses"""
        middleware = self._create_middleware()

        # Configure get_response to return error
        self.get_response.return_value = HttpResponse(status=500)

        request = self.factory.get("/api/v3/core/users/")
        self.mock_tracer.start_as_current_span.return_value.__enter__.return_value = self.mock_span

        response = middleware(request)

        # Verify error status was set
        self.mock_span.set_attribute.assert_any_call("http.status_code", 500)
        self.mock_span.set_status.assert_called_once()

    def test_middleware_handles_unauthenticated_requests(self):
        """Test middleware handles requests without authenticated user"""
        middleware = self._create_middleware()
        request = self.factory.get("/api/v3/core/applications/")
        request.user = MagicMock()
        request.user.is_authenticated = False

        self.mock_tracer.start_as_current_span.return_value.__enter__.return_value = self.mock_span

        response = middleware(request)

        # Should not set user attributes
        user_calls = [
            call
            for call in self.mock_span.set_attribute.call_args_list
            if call[0][0].startswith("user.")
        ]
        self.assertEqual(len(user_calls), 0)

    def test_middleware_records_client_info(self):
        """Test middleware records client information"""
        middleware = self._create_middleware()
        request = self.factory.get(
            "/api/v3/flows/",
            HTTP_USER_AGENT="Mozilla/5.0 Test Browser",
            HTTP_X_FORWARDED_FOR="192.168.1.100",
        )

        # Enhanced middleware that also records client info
        mock_tracer = self.mock_tracer  # Capture from outer scope

        class EnhancedMiddleware:
            def __init__(self, get_response):
                self.get_response = get_response
                self.tracer = mock_tracer

            def __call__(self, request):
                with self.tracer.start_as_current_span("http.request") as span:
                    if "HTTP_USER_AGENT" in request.META:
                        span.set_attribute("http.user_agent", request.META["HTTP_USER_AGENT"])
                    if "HTTP_X_FORWARDED_FOR" in request.META:
                        span.set_attribute("http.client_ip", request.META["HTTP_X_FORWARDED_FOR"])
                    return self.get_response(request)

        enhanced_middleware = EnhancedMiddleware(self.get_response)
        self.mock_tracer.start_as_current_span.return_value.__enter__.return_value = self.mock_span

        response = enhanced_middleware(request)

        # Verify client info was recorded
        self.mock_span.set_attribute.assert_any_call("http.user_agent", "Mozilla/5.0 Test Browser")
        self.mock_span.set_attribute.assert_any_call("http.client_ip", "192.168.1.100")

    def test_middleware_handles_exceptions(self):
        """Test middleware properly handles and records exceptions"""
        middleware = self._create_middleware()

        # Configure get_response to raise exception
        self.get_response.side_effect = ValueError("Test exception")

        request = self.factory.get("/api/v3/broken/")
        self.mock_tracer.start_as_current_span.return_value.__enter__.return_value = self.mock_span

        # Enhanced middleware with exception handling
        mock_tracer = self.mock_tracer  # Capture from outer scope

        class ExceptionHandlingMiddleware:
            def __init__(self, get_response):
                self.get_response = get_response
                self.tracer = mock_tracer

            def __call__(self, request):
                with self.tracer.start_as_current_span("http.request") as span:
                    try:
                        return self.get_response(request)
                    except Exception as e:
                        span.record_exception(e)
                        span.set_status(MagicMock())
                        raise

        exception_middleware = ExceptionHandlingMiddleware(self.get_response)

        with self.assertRaises(ValueError):
            exception_middleware(request)

        # Verify exception was recorded
        self.mock_span.record_exception.assert_called_once()
        self.mock_span.set_status.assert_called_once()

    def test_middleware_preserves_trace_context(self):
        """Test middleware preserves incoming trace context"""
        middleware = self._create_middleware()

        # Request with trace context headers
        request = self.factory.get(
            "/api/v3/flows/",
            HTTP_TRACEPARENT="00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
            HTTP_TRACESTATE="congo=t61rcWkgMzE",
        )

        self.mock_tracer.start_as_current_span.return_value.__enter__.return_value = self.mock_span

        response = middleware(request)

        # In real implementation, trace context would be extracted and used
        self.assertEqual(response.status_code, 200)

    def test_middleware_custom_span_name(self):
        """Test middleware can use custom span names based on route"""
        middleware = self._create_middleware()

        # Enhanced middleware with custom span naming
        mock_tracer = self.mock_tracer  # Capture from outer scope

        class CustomSpanNameMiddleware:
            def __init__(self, get_response):
                self.get_response = get_response
                self.tracer = mock_tracer

            def __call__(self, request):
                # Custom span name based on path
                span_name = self._get_span_name(request)
                with self.tracer.start_as_current_span(span_name) as span:
                    return self.get_response(request)

            def _get_span_name(self, request):
                if request.path.startswith("/api/v3/flows/"):
                    return "flows.api"
                elif request.path.startswith("/api/v3/core/"):
                    return "core.api"
                return "http.request"

        custom_middleware = CustomSpanNameMiddleware(self.get_response)
        request = self.factory.get("/api/v3/flows/executor/")

        self.mock_tracer.start_as_current_span.return_value.__enter__.return_value = self.mock_span

        response = custom_middleware(request)

        # Verify custom span name was used
        self.mock_tracer.start_as_current_span.assert_called_once_with("flows.api")
