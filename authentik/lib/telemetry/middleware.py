"""OpenTelemetry middleware for Django"""

import re
import time
import logging
from typing import Callable, Optional

from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin

from authentik.lib.telemetry import provider

logger = logging.getLogger(__name__)


class OpenTelemetryMiddleware(MiddlewareMixin):
    """Django middleware for OpenTelemetry tracing"""

    def __init__(self, get_response: Callable):
        super().__init__(get_response)
        self.get_response = get_response
        self.tracer = None
        self.sampler = provider.AdaptiveSampler()

        # Patterns for requests to exclude from tracing
        self.excluded_patterns = [
            re.compile(r"/health/?$"),
            re.compile(r"/metrics/?$"),
            re.compile(r"/readiness/?$"),
            re.compile(r"/liveness/?$"),
            re.compile(r"/static/.*"),
            re.compile(r"/media/.*"),
        ]

        # Initialize tracer if telemetry is enabled
        if provider.provider.is_enabled():
            provider.provider.initialize()
            self.tracer = provider.provider.get_tracer("authentik.middleware")

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process request with OpenTelemetry tracing"""
        if not self.tracer or self._should_exclude_request(request):
            return self.get_response(request)

        # Create span for the request
        span_name = self._get_span_name(request)

        with self.tracer.start_as_current_span(span_name) as span:
            # Record request attributes
            self._set_request_attributes(span, request)

            start_time = time.time()
            try:
                response = self.get_response(request)

                # Record response attributes
                self._set_response_attributes(span, response)

                return response

            except Exception as exc:
                # Record exception details
                span.record_exception(exc)
                span.set_status(self._get_error_status(exc))
                raise

            finally:
                # Record request duration
                duration = time.time() - start_time
                span.set_attribute("http.response_time", duration)

    def _should_exclude_request(self, request: HttpRequest) -> bool:
        """Check if request should be excluded from tracing"""
        path = request.path_info

        for pattern in self.excluded_patterns:
            if pattern.match(path):
                return True

        return False

    def _get_span_name(self, request: HttpRequest) -> str:
        """Generate span name for the request"""
        method = request.method
        path = request.path_info

        # Simplify common API patterns
        if path.startswith("/api/v3/"):
            # Extract API endpoint
            parts = path.split("/")
            if len(parts) >= 4:
                return f"{method} /api/v3/{parts[3]}"

        return f"{method} {path}"

    def _set_request_attributes(self, span, request: HttpRequest):
        """Set request-related span attributes"""
        try:
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", request.build_absolute_uri())
            span.set_attribute("http.route", request.path_info)
            span.set_attribute("http.scheme", request.scheme)

            # User agent
            user_agent = request.META.get("HTTP_USER_AGENT")
            if user_agent:
                span.set_attribute("http.user_agent", user_agent)

            # Client IP
            client_ip = self._get_client_ip(request)
            if client_ip:
                span.set_attribute("http.client_ip", client_ip)

            # User information if available
            if hasattr(request, "user") and request.user and hasattr(request.user, "pk"):
                if request.user.is_authenticated:
                    span.set_attribute("user.id", str(request.user.pk))
                    span.set_attribute("user.username", getattr(request.user, "username", ""))

        except Exception as exc:
            logger.warning("Failed to set request attributes", exc_info=exc)

    def _set_response_attributes(self, span, response: HttpResponse):
        """Set response-related span attributes"""
        try:
            span.set_attribute("http.status_code", response.status_code)

            # Set status based on HTTP status code
            if response.status_code >= 400:
                span.set_status(self._get_error_status_from_code(response.status_code))

            # Content type
            content_type = response.get("Content-Type", "")
            if content_type:
                span.set_attribute("http.response.content_type", content_type)

        except Exception as exc:
            logger.warning("Failed to set response attributes", exc_info=exc)

    def _get_client_ip(self, request: HttpRequest) -> Optional[str]:
        """Extract client IP from request"""
        # Check X-Forwarded-For header
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()

        # Check X-Real-IP header
        x_real_ip = request.META.get("HTTP_X_REAL_IP")
        if x_real_ip:
            return x_real_ip

        # Fall back to REMOTE_ADDR
        return request.META.get("REMOTE_ADDR")

    def _get_error_status(self, exc: Exception):
        """Get OpenTelemetry status for an exception"""
        try:
            from opentelemetry.trace import Status, StatusCode

            return Status(StatusCode.ERROR, str(exc))
        except ImportError:
            return None

    def _get_error_status_from_code(self, status_code: int):
        """Get OpenTelemetry status for HTTP status code"""
        try:
            from opentelemetry.trace import Status, StatusCode

            if status_code >= 500:
                return Status(StatusCode.ERROR, f"HTTP {status_code}")
            elif status_code >= 400:
                return Status(StatusCode.ERROR, f"HTTP {status_code}")
            return Status(StatusCode.OK)
        except ImportError:
            return None
