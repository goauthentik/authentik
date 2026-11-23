"""authentik core error views"""

from django.http.response import (
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseNotFound,
    HttpResponseServerError,
)
from django.template.response import TemplateResponse
from django.views.generic import TemplateView


class BadRequestTemplateResponse(TemplateResponse, HttpResponseBadRequest):
    """Combine Template response with Http Code 400"""


class ForbiddenTemplateResponse(TemplateResponse, HttpResponseForbidden):
    """Combine Template response with Http Code 403"""


class NotFoundTemplateResponse(TemplateResponse, HttpResponseNotFound):
    """Combine Template response with Http Code 404"""


class ServerErrorTemplateResponse(TemplateResponse, HttpResponseServerError):
    """Combine Template response with Http Code 500"""


class ErrorView(TemplateView):
    """Base for the views wired up as django's handler400/403/404/500.

    Django invokes an error handler with the request that failed, whatever its
    method. A plain TemplateView only implements `get`, so its `dispatch` answers
    a failing POST/PUT/PATCH/DELETE with 405 Method Not Allowed and discards the
    handler's own status code -- which is how an API error surfaced as a 405 with
    an `Allow: GET, HEAD, OPTIONS` header. Render the page for every method so the
    status code the handler stands for is the one the client sees.
    """

    template_name = "if/error.html"

    def dispatch(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)


class BadRequestView(ErrorView):
    """Show Bad Request message"""

    extra_context = {"title": "Bad Request"}

    response_class = BadRequestTemplateResponse


class ForbiddenView(ErrorView):
    """Show Forbidden message"""

    extra_context = {"title": "Forbidden"}

    response_class = ForbiddenTemplateResponse


class NotFoundView(ErrorView):
    """Show Not Found message"""

    extra_context = {"title": "Not Found"}

    response_class = NotFoundTemplateResponse


class ServerErrorView(ErrorView):
    """Show Server Error message"""

    extra_context = {"title": "Server Error"}

    response_class = ServerErrorTemplateResponse
