"""Sentry tunnel"""
from json import loads

from django.conf import settings
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.views.generic.base import View
from requests import post
from requests.exceptions import RequestException

from authentik.lib.config import CONFIG


class SentryTunnelView(View):
    """Sentry tunnel, to prevent ad blockers from blocking sentry"""

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Sentry tunnel, to prevent ad blockers from blocking sentry"""
        # Only allow usage of this endpoint when error reporting is enabled
        if not CONFIG.y_bool("error_reporting.enabled", False):
            return HttpResponse(status=400)
        # Body is 2 json objects separated by \n
        full_body = request.body
        header = loads(full_body.splitlines()[0])
        # Check that the DSN is what we expect
        dsn = header.get("dsn", "")
        if dsn != settings.SENTRY_DSN:
            return HttpResponse(status=400)
        response = post(
            "https://sentry.beryju.org/api/8/envelope/",
            data=full_body,
            headers={"Content-Type": "application/octet-stream"},
        )
        try:
            response.raise_for_status()
        except RequestException:
            return HttpResponse(status=500)
        return HttpResponse(status=response.status_code)
