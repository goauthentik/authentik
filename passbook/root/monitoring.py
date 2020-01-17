"""Metrics view"""
from base64 import b64encode

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.views import View
from django_prometheus.exports import ExportToDjangoView


class MetricsView(View):
    """Wrapper around ExportToDjangoView, using http-basic auth"""

    def get(self, request: HttpRequest) -> HttpResponse:
        """Check for HTTP-Basic auth"""
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        auth_type, _, credentials = auth_header.partition(" ")
        credentials = f"monitor:{settings.SECRET_KEY}"
        expected = b64encode(str.encode(credentials)).decode()

        if auth_type != "Basic" or credentials != expected:
            response = HttpResponse(status=401)
            response['WWW-Authenticate'] = 'Basic realm="passbook-monitoring"'
            return response

        return ExportToDjangoView(request)
