"""passbook impersonation views"""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from structlog import get_logger

from passbook.core.middleware import (
    SESSION_IMPERSONATE_ORIGINAL_USER,
    SESSION_IMPERSONATE_USER,
)
from passbook.core.models import User

LOGGER = get_logger()


class ImpersonateInitView(View):
    """Initiate Impersonation"""

    def get(self, request: HttpRequest, user_id: int) -> HttpResponse:
        """Impersonation handler, checks permissions"""
        if not request.user.has_perm("impersonate"):
            LOGGER.debug(
                "User attempted to impersonate without permissions", user=request.user
            )
            return HttpResponse("Unauthorized", status=401)

        user_to_be = get_object_or_404(User, pk=user_id)

        request.session[SESSION_IMPERSONATE_ORIGINAL_USER] = request.user
        request.session[SESSION_IMPERSONATE_USER] = user_to_be

        # TODO Audit log entry

        return redirect("passbook_core:overview")


class ImpersonateEndView(View):
    """End User impersonation"""

    def get(self, request: HttpRequest) -> HttpResponse:
        """End Impersonation handler"""
        if (
            SESSION_IMPERSONATE_USER not in request.session
            or SESSION_IMPERSONATE_ORIGINAL_USER not in request.session
        ):
            LOGGER.debug("Can't end impersonation", user=request.user)
            return redirect("passbook_core:overview")

        del request.session[SESSION_IMPERSONATE_USER]
        del request.session[SESSION_IMPERSONATE_ORIGINAL_USER]

        # TODO: Audit log entry

        return redirect("passbook_core:overview")
