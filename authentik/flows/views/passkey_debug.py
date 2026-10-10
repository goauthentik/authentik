"""Temporary passkey autofill diagnostics. Drop this before merging."""

from json import loads

from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from structlog.stdlib import get_logger

LOGGER = get_logger()
MAX_BODY_BYTES = 64 * 1024


@method_decorator(csrf_exempt, name="dispatch")
class PasskeyDebugView(View):
    """Write passkey debug entries sent by the login page to the server log. The login page is
    unauthenticated, so this accepts anonymous requests and caps the body size."""

    def post(self, request: HttpRequest) -> HttpResponse:
        if len(request.body) > MAX_BODY_BYTES:
            return HttpResponseBadRequest()
        try:
            payload = loads(request.body)
        except ValueError:
            return HttpResponseBadRequest()
        if not isinstance(payload, dict):
            return HttpResponseBadRequest()
        for entry in payload.get("entries", []):
            LOGGER.info(
                "passkey debug",
                page=payload.get("page"),
                url=payload.get("url"),
                user_agent=payload.get("userAgent"),
                entry=entry,
            )
        return HttpResponse(status=204)
