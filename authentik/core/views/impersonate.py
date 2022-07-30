"""authentik impersonation views"""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from structlog.stdlib import get_logger

from authentik.core.middleware import (
    SESSION_KEY_IMPERSONATE_ORIGINAL_USER,
    SESSION_KEY_IMPERSONATE_USER,
)
from authentik.core.models import User
from authentik.events.models import Event, EventAction
from authentik.lib.config import CONFIG

LOGGER = get_logger()


class ImpersonateInitView(View):
    """Initiate Impersonation"""

    def get(self, request: HttpRequest, user_id: int) -> HttpResponse:
        """Impersonation handler, checks permissions"""
        if not CONFIG.y_bool("impersonation"):
            LOGGER.debug("User attempted to impersonate", user=request.user)
            return HttpResponse("Unauthorized", status=401)
        if not request.user.has_perm("impersonate"):
            LOGGER.debug("User attempted to impersonate without permissions", user=request.user)
            return HttpResponse("Unauthorized", status=401)

        user_to_be = get_object_or_404(User, pk=user_id)

        request.session[SESSION_KEY_IMPERSONATE_ORIGINAL_USER] = request.user
        request.session[SESSION_KEY_IMPERSONATE_USER] = user_to_be

        Event.new(EventAction.IMPERSONATION_STARTED).from_http(request, user_to_be)

        return redirect("authentik_core:if-user")


class ImpersonateEndView(View):
    """End User impersonation"""

    def get(self, request: HttpRequest) -> HttpResponse:
        """End Impersonation handler"""
        if (
            SESSION_KEY_IMPERSONATE_USER not in request.session
            or SESSION_KEY_IMPERSONATE_ORIGINAL_USER not in request.session
        ):
            LOGGER.debug("Can't end impersonation", user=request.user)
            return redirect("authentik_core:if-user")

        original_user = request.session[SESSION_KEY_IMPERSONATE_ORIGINAL_USER]

        del request.session[SESSION_KEY_IMPERSONATE_USER]
        del request.session[SESSION_KEY_IMPERSONATE_ORIGINAL_USER]

        Event.new(EventAction.IMPERSONATION_ENDED).from_http(request, original_user)

        return redirect("authentik_core:root-redirect")
