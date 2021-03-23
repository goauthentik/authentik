"""Email stage views"""
from django.http.request import HttpRequest
from django.http.response import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from structlog.stdlib import get_logger

from authentik.core.models import Token
from authentik.flows.views import SESSION_KEY_GET
from authentik.stages.email.stage import QS_KEY_TOKEN

LOGGER = get_logger()


class FromEmailView(View):
    """FromEmailView, this view is linked in the email confirmation link.
    It is required because the flow executor does not pass query args to the API,
    so this view gets called, checks for a Querystring and updates the plan
    if everything is valid."""

    def get(self, request: HttpRequest, flow_slug: str) -> HttpResponse:
        """Check for ?token param and validate it."""
        if QS_KEY_TOKEN not in request.GET:
            LOGGER.debug("No token set")
            return HttpResponseBadRequest()
        # Lookup token here to quickly fail for invalid input
        get_object_or_404(Token, pk=request.GET[QS_KEY_TOKEN])
        if SESSION_KEY_GET not in request.session:
            request.session[SESSION_KEY_GET] = {}
        request.session[SESSION_KEY_GET][QS_KEY_TOKEN] = request.GET[QS_KEY_TOKEN]
        return redirect("authentik_core:if-flow", flow_slug=flow_slug)
