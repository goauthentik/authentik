"""authentik helper views"""

from django.http import HttpRequest
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _


def bad_request_message(
    request: HttpRequest,
    message: str,
    title="Bad Request",
    template="if/error.html",
) -> TemplateResponse:
    """Return generic error page with message, with status code set to 400"""
    return TemplateResponse(
        request,
        template,
        {"message": message, "title": _(title)},
        status=400,
    )
