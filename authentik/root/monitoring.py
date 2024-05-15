"""Metrics view"""

from base64 import b64encode

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

        return ExportToDjangoView(request)


class LiveView(View):
    """View for liveness probe, always returns Http 204"""

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        return HttpResponse(status=204)


class ReadyView(View):
    """View for readiness probe, always returns Http 204, unless sql or redis is down"""

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
        return HttpResponse(status=204)
