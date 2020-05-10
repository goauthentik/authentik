"""passbook multi-stage authentication engine"""
from datetime import timedelta

from django.contrib import messages
from django.http import HttpRequest
from django.shortcuts import reverse
from django.utils.http import urlencode
from django.utils.timezone import now
from django.utils.translation import gettext as _
from structlog import get_logger

from passbook.core.models import Nonce
from passbook.flows.planner import PLAN_CONTEXT_PENDING_USER
from passbook.flows.stage import AuthenticationStage
from passbook.stages.email.tasks import send_mails
from passbook.stages.email.utils import TemplateEmailMessage

LOGGER = get_logger()


class EmailStageView(AuthenticationStage):
    """E-Mail stage which sends E-Mail for verification"""

    template_name = "stages/email/waiting_message.html"

    def get_full_url(self, **kwargs) -> str:
        """Get full URL to be used in template"""
        base_url = reverse(
            "passbook_flows:flow-executor",
            kwargs={"flow_slug": self.executor.flow.slug},
        )
        relative_url = f"{base_url}?{urlencode(kwargs)}"
        return self.request.build_absolute_uri(relative_url)

    def get(self, request, *args, **kwargs):
        # TODO: Form to make sure email is only sent once
        pending_user = self.executor.plan.context[PLAN_CONTEXT_PENDING_USER]
        # TODO: Get expiry from Stage setting
        valid_delta = timedelta(
            minutes=31
        )  # 31 because django timesince always rounds down
        nonce = Nonce.objects.create(user=pending_user, expires=now() + valid_delta)
        # Send mail to user
        message = TemplateEmailMessage(
            subject=_("passbook - Password Recovery"),
            template_name="stages/email/for_email/password_reset.html",
            to=[pending_user.email],
            template_context={
                "url": self.get_full_url(token=nonce.pk.hex),
                "user": pending_user,
                "expires": nonce.expires,
            },
        )
        send_mails(self.executor.current_stage, message)
        messages.success(request, _("Check your E-Mails for a password reset link."))
        # We can't call stage_ok yet, as we're still waiting
        # for the user to click the link in the email
        # return self.executor.stage_ok()
        return super().get(request, *args, **kwargs)

    def post(self, request: HttpRequest):
        """Just redirect to next stage"""
        return self.executor.stage_ok()
