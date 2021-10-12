"""Metrics view"""
from base64 import b64encode
from typing import Callable

from django.conf import settings
from django.db import connections
from django.db.utils import OperationalError
from django.http import HttpRequest, HttpResponse
from django.views import View
from django_prometheus.exports import ExportToDjangoView
from django_redis import get_redis_connection
from prometheus_client import Gauge
from redis.exceptions import RedisError

from authentik.admin.api.workers import GAUGE_WORKERS
from authentik.events.monitored_tasks import TaskInfo
from authentik.root.celery import CELERY_APP


class UpdatingGauge(Gauge):
    """Gauge which fetches its own value from an update function.

    Update function is called on instantiate"""

    def __init__(self, *args, update_func: Callable, **kwargs):
        super().__init__(*args, **kwargs)
        self._update_func = update_func
        self.update()

    def update(self):
        """Set value from update function"""
        val = self._update_func()
        if val:
            self.set(val)


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

        count = len(CELERY_APP.control.ping(timeout=0.5))
        GAUGE_WORKERS.set(count)

        for task in TaskInfo.all().values():
            task.set_prom_metrics()

        return ExportToDjangoView(request)


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
