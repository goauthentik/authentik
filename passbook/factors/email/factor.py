"""passbook multi-factor authentication engine"""
from django.contrib import messages
from django.http import HttpRequest
from django.shortcuts import reverse
from django.utils.translation import gettext as _
from structlog import get_logger

from passbook.core.models import Nonce
from passbook.factors.email.tasks import send_mails
from passbook.factors.email.utils import TemplateEmailMessage
from passbook.flows.factor_base import AuthenticationFactor
from passbook.flows.planner import PLAN_CONTEXT_PENDING_USER
from passbook.lib.config import CONFIG

LOGGER = get_logger()


class EmailFactorView(AuthenticationFactor):
    """Dummy factor for testing with multiple factors"""

    def get_context_data(self, **kwargs):
        kwargs["show_password_forget_notice"] = CONFIG.y(
            "passbook.password_reset.enabled"
        )
        return super().get_context_data(**kwargs)

    def get(self, request, *args, **kwargs):
        pending_user = self.executor.plan.context[PLAN_CONTEXT_PENDING_USER]
        nonce = Nonce.objects.create(user=pending_user)
        # Send mail to user
        message = TemplateEmailMessage(
            subject=_("Forgotten password"),
            template_name="email/account_password_reset.html",
            to=[pending_user.email],
            template_context={
                "url": self.request.build_absolute_uri(
                    reverse(
                        "passbook_core:auth-password-reset",
                        kwargs={"nonce": nonce.uuid},
                    )
                )
            },
        )
        send_mails(self.executor.current_factor, message)
        messages.success(request, _("Check your E-Mails for a password reset link."))
        return self.executor.cancel()

    def post(self, request: HttpRequest):
        """Just redirect to next factor"""
        return self.executor.factor_ok()
