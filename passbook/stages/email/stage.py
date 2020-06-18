"""passbook multi-stage authentication engine"""
from datetime import timedelta

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, reverse
from django.utils.http import urlencode
from django.utils.timezone import now
from django.utils.translation import gettext as _
from django.views.generic import FormView
from structlog import get_logger

from passbook.core.models import Token
from passbook.flows.planner import PLAN_CONTEXT_PENDING_USER
from passbook.flows.stage import StageView
from passbook.stages.email.forms import EmailStageSendForm
from passbook.stages.email.tasks import send_mails
from passbook.stages.email.utils import TemplateEmailMessage

LOGGER = get_logger()
QS_KEY_TOKEN = "token"


class EmailStageView(FormView, StageView):
    """Email stage which sends Email for verification"""

    form_class = EmailStageSendForm
    template_name = "stages/email/waiting_message.html"

    def get_full_url(self, **kwargs) -> str:
        """Get full URL to be used in template"""
        base_url = reverse(
            "passbook_flows:flow-executor",
            kwargs={"flow_slug": self.executor.flow.slug},
        )
        relative_url = f"{base_url}?{urlencode(kwargs)}"
        return self.request.build_absolute_uri(relative_url)

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if QS_KEY_TOKEN in request.GET:
            token = get_object_or_404(Token, pk=request.GET[QS_KEY_TOKEN])
            self.executor.plan.context[PLAN_CONTEXT_PENDING_USER] = token.user
            token.delete()
            messages.success(request, _("Successfully verified Email."))
            return self.executor.stage_ok()
        return super().get(request, *args, **kwargs)

    def form_invalid(self, form: EmailStageSendForm) -> HttpResponse:
        if PLAN_CONTEXT_PENDING_USER not in self.executor.plan.context:
            messages.error(self.request, _("No pending user."))
            return super().form_invalid(form)
        pending_user = self.executor.plan.context[PLAN_CONTEXT_PENDING_USER]
        valid_delta = timedelta(
            minutes=self.executor.current_stage.token_expiry + 1
        )  # + 1 because django timesince always rounds down
        token = Token.objects.create(user=pending_user, expires=now() + valid_delta)
        # Send mail to user
        message = TemplateEmailMessage(
            subject=_("passbook - Password Recovery"),
            template_name=self.executor.current_stage.template,
            to=[pending_user.email],
            template_context={
                "url": self.get_full_url(**{QS_KEY_TOKEN: token.pk.hex}),
                "user": pending_user,
                "expires": token.expires,
            },
        )
        send_mails(self.executor.current_stage, message)
        # We can't call stage_ok yet, as we're still waiting
        # for the user to click the link in the email
        return super().form_invalid(form)
