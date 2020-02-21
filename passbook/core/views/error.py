"""passbook core error views"""

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


class BadRequestView(TemplateView):
    """Show Bad Request message"""

    extra_context = {"card_title": "Bad Request"}

    response_class = BadRequestTemplateResponse
    template_name = "error/generic.html"


class ForbiddenView(TemplateView):
    """Show Forbidden message"""

    extra_context = {"card_title": "Forbidden"}

    response_class = ForbiddenTemplateResponse
    template_name = "error/generic.html"


class NotFoundView(TemplateView):
    """Show Not Found message"""

    extra_context = {"card_title": "Not Found"}

    response_class = NotFoundTemplateResponse
    template_name = "error/generic.html"


class ServerErrorView(TemplateView):
    """Show Server Error message"""

    extra_context = {"card_title": "Server Error"}

    response_class = ServerErrorTemplateResponse
    template_name = "error/generic.html"

    # pylint: disable=useless-super-delegation
    def dispatch(self, *args, **kwargs):
        """Little wrapper so django accepts this function"""
        return super().dispatch(*args, **kwargs)
