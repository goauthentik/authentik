"""Metrics view"""

from django.db import connections
from django.db.utils import OperationalError
from django.dispatch import Signal
from django.http import HttpRequest, HttpResponse
from django.views import View
from django_prometheus.exports import ExportToDjangoView

monitoring_set = Signal()


class MetricsView(View):
    """Wrapper around ExportToDjangoView with authentication, accessed by the authentik router"""

    def get(self, request: HttpRequest) -> HttpResponse:
        """Check for HTTP-Basic auth"""
        monitoring_set.send_robust(self)
        return ExportToDjangoView(request)


class LiveView(View):
    """View for liveness probe, always returns Http 200"""

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        return HttpResponse(status=200)


class ReadyView(View):
    """View for readiness probe, always returns Http 200, unless sql is down"""

    def check_db(self):
        for db_conn in connections.all():
            # Force connection reload
            db_conn.connect()
            _ = db_conn.cursor()

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        try:
            self.check_db()
        except OperationalError:  # pragma: no cover
            return HttpResponse(status=503)
        return HttpResponse(status=200)
