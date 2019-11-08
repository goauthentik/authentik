"""Metrics view"""
from base64 import b64encode

from django.conf import settings
from django.http import Http404, HttpRequest, HttpResponse
from django.views import View
from django_prometheus.exports import ExportToDjangoView


class MetricsView(View):
    """Wrapper around ExportToDjangoView, using http-basic auth"""

    def get(self, request: HttpRequest) -> HttpResponse:
        """Check for HTTP-Basic auth"""
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        token_type, _, credentials = auth_header.partition(' ')
        creds = f"monitor:{settings.SECRET_KEY}"
        expected = b64encode(str.encode(creds)).decode()

        if token_type != 'Basic' or credentials != expected:
            raise Http404

        return ExportToDjangoView(request)
