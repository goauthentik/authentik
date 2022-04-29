"""Metrics view"""
from base64 import b64encode

import prometheus_client
from django.conf import settings
from django.db import connections
from django.db.utils import OperationalError
from django.dispatch import Signal
from django.http import HttpRequest, HttpResponse
from django.views import View
from django_redis import get_redis_connection
from prometheus_client import multiprocess
from redis.exceptions import RedisError

monitoring_set = Signal()


class MetricsView(View):
    """Wrapper around ExportToDjangoView, using http-basic auth"""

    def get(self, request: HttpRequest) -> HttpResponse:
        """Check for HTTP-Basic auth"""
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        auth_type, _, given_credentials = auth_header.partition(" ")
        credentials = f"monitor:{settings.SECRET_KEY}"
        expected = b64encode(str.encode(credentials)).decode()
        authed = auth_type == "Basic" and given_credentials == expected
        if not authed and not settings.DEBUG:
            response = HttpResponse(status=401)
            response["WWW-Authenticate"] = 'Basic realm="authentik-monitoring"'
            return response

        monitoring_set.send_robust(self)

        registry = prometheus_client.CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        try:
            metrics_page = prometheus_client.generate_latest(registry)
            return HttpResponse(metrics_page, content_type=prometheus_client.CONTENT_TYPE_LATEST)
        except (UnicodeDecodeError, KeyError):
            return HttpResponse(status_code=500)


class LiveView(View):
    """View for liveness probe, always returns Http 204"""

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        return HttpResponse(status=204)


class ReadyView(View):
    """View for readiness probe, always returns Http 204, unless sql or redis is down"""

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        try:
            db_conn = connections["default"]
            _ = db_conn.cursor()
        except OperationalError:
            return HttpResponse(status=503)
        try:
            redis_conn = get_redis_connection()
            redis_conn.ping()
        except RedisError:
            return HttpResponse(status=503)
        return HttpResponse(status=204)
