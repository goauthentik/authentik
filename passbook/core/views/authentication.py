"""passbook core authentication views"""
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, reverse
from django.utils.translation import ugettext as _
from django.views import View
from structlog import get_logger

from passbook.core.models import Nonce

LOGGER = get_logger()


class LogoutView(LoginRequiredMixin, View):
    """Log current user out"""

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        """Log current user out"""
        logout(request)
        messages.success(request, _("You've successfully been logged out."))
        return redirect(reverse("passbook_core:auth-login"))


class PasswordResetView(View):
    """Temporarily authenticate User and allow them to reset their password"""

    def get(self, request: HttpRequest, nonce_uuid: str) -> HttpResponse:
        """Authenticate user with nonce and redirect to password change view"""
        # 3. (Optional) Trap user in password change view
        nonce = get_object_or_404(Nonce, uuid=nonce_uuid)
        # Workaround: hardcoded reference to ModelBackend, needs testing
        nonce.user.backend = "django.contrib.auth.backends.ModelBackend"
        login(request, nonce.user)
        nonce.delete()
        messages.success(
            request, _(("Temporarily authenticated, please change your password")),
        )
        return redirect("passbook_core:user-change-password")
