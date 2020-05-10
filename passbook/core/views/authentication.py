"""passbook core authentication views"""
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, reverse
from django.utils.translation import ugettext as _
from django.views import View
from structlog import get_logger

LOGGER = get_logger()


class LogoutView(LoginRequiredMixin, View):
    """Log current user out"""

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        """Log current user out"""
        logout(request)
        messages.success(request, _("You've successfully been logged out."))
        return redirect(reverse("passbook_flows:default-auth"))
