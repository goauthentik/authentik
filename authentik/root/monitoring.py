"""Metrics view"""

from hmac import compare_digest
from pathlib import Path
from tempfile import gettempdir

from django.conf import settings
from django.db import connections
from django.db.utils import OperationalError
from django.dispatch import Signal
from django.http import HttpRequest, HttpResponse
from django.views import View
from django_prometheus.exports import ExportToDjangoView
from django_redis import get_redis_connection
from redis.exceptions import RedisError

monitoring_set = Signal()


class MetricsView(View):
    """Wrapper around ExportToDjangoView with authentication, accessed by the authentik router"""

    def __init__(self, **kwargs):
        _tmp = Path(gettempdir())
        with open(_tmp / "authentik-core-metrics.key") as _f:
            self.monitoring_key = _f.read()

    def get(self, request: HttpRequest) -> HttpResponse:
        """Check for HTTP-Basic auth"""
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        auth_type, _, given_credentials = auth_header.partition(" ")
        authed = auth_type == "Bearer" and compare_digest(given_credentials, self.monitoring_key)
        if not authed and not settings.DEBUG:
            return HttpResponse(status=401)
        monitoring_set.send_robust(self)
        return ExportToDjangoView(request)


class LiveView(View):
    """View for liveness probe, always returns Http 200"""

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        return HttpResponse(status=200)


class ReadyView(View):
    """View for readiness probe, always returns Http 200, unless sql or redis is down"""

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        try:
            for db_conn in connections.all():
                _ = db_conn.cursor()
        except OperationalError:  # pragma: no cover
            return HttpResponse(status=503)
        try:
            redis_conn = get_redis_connection()
            redis_conn.ping()
        except RedisError:  # pragma: no cover
            return HttpResponse(status=503)
        return HttpResponse(status=200)
