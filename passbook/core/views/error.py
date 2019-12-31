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

    response_class = BadRequestTemplateResponse
    template_name = "error/400.html"

    extra_context = {"is_login": True}


class ForbiddenView(TemplateView):
    """Show Forbidden message"""

    response_class = ForbiddenTemplateResponse
    template_name = "error/403.html"

    extra_context = {"is_login": True}


class NotFoundView(TemplateView):
    """Show Not Found message"""

    response_class = NotFoundTemplateResponse
    template_name = "error/404.html"

    extra_context = {"is_login": True}


class ServerErrorView(TemplateView):
    """Show Server Error message"""

    response_class = ServerErrorTemplateResponse
    template_name = "error/500.html"

    extra_context = {"is_login": True}

    # pylint: disable=useless-super-delegation
    def dispatch(self, *args, **kwargs):
        """Little wrapper so django accepts this function"""
        return super().dispatch(*args, **kwargs)
