"""authentik multi-stage authentication engine"""
from datetime import timedelta

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.text import slugify
from django.utils.timezone import now
from django.utils.translation import gettext as _
from rest_framework.fields import CharField
from rest_framework.serializers import ValidationError
from structlog.stdlib import get_logger

from authentik.core.models import Token
from authentik.flows.challenge import Challenge, ChallengeResponse, ChallengeTypes
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import ChallengeStageView
from authentik.flows.views.executor import SESSION_KEY_GET
from authentik.stages.email.models import EmailStage
from authentik.stages.email.tasks import send_mails
from authentik.stages.email.utils import TemplateEmailMessage

LOGGER = get_logger()
QS_KEY_TOKEN = "etoken"  # nosec
PLAN_CONTEXT_EMAIL_SENT = "email_sent"


class EmailChallenge(Challenge):
    """Email challenge"""

    component = CharField(default="ak-stage-email")


class EmailChallengeResponse(ChallengeResponse):
    """Email challenge resposen. No fields. This challenge is
    always declared invalid to give the user a chance to retry"""

    component = CharField(default="ak-stage-email")

    def validate(self, attrs):
        raise ValidationError(detail="email-sent", code="email-sent")


class EmailStageView(ChallengeStageView):
    """Email stage which sends Email for verification"""

    response_class = EmailChallengeResponse

    def get_full_url(self, **kwargs) -> str:
        """Get full URL to be used in template"""
        base_url = reverse(
            "authentik_core:if-flow",
            kwargs={"flow_slug": self.executor.flow.slug},
        )
        relative_url = f"{base_url}?{urlencode(kwargs)}"
        return self.request.build_absolute_uri(relative_url)

    def get_token(self) -> Token:
        """Get token"""
        pending_user = self.executor.plan.context[PLAN_CONTEXT_PENDING_USER]
        current_stage: EmailStage = self.executor.current_stage
        valid_delta = timedelta(
            minutes=current_stage.token_expiry + 1
        )  # + 1 because django timesince always rounds down
        token_filters = {
            "user": pending_user,
            "identifier": slugify(f"ak-email-stage-{current_stage.name}-{pending_user}"),
        }
        # Don't check for validity here, we only care if the token exists
        tokens = Token.objects.filter(**token_filters)
        if not tokens.exists():
            return Token.objects.create(expires=now() + valid_delta, **token_filters)
        token = tokens.first()
        # Check if token is expired and rotate key if so
        if token.is_expired:
            token.expire_action()
        return token

    def send_email(self):
        """Helper function that sends the actual email. Implies that you've
        already checked that there is a pending user."""
        pending_user = self.executor.plan.context[PLAN_CONTEXT_PENDING_USER]
        current_stage: EmailStage = self.executor.current_stage
        token = self.get_token()
        # Send mail to user
        message = TemplateEmailMessage(
            subject=_(current_stage.subject),
            template_name=current_stage.template,
            to=[pending_user.email],
            template_context={
                "url": self.get_full_url(**{QS_KEY_TOKEN: token.key}),
                "user": pending_user,
                "expires": token.expires,
            },
        )
        send_mails(current_stage, message)

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        # Check if the user came back from the email link to verify
        if QS_KEY_TOKEN in request.session.get(SESSION_KEY_GET, {}):
            tokens = Token.filter_not_expired(key=request.session[SESSION_KEY_GET][QS_KEY_TOKEN])
            if not tokens.exists():
                return self.executor.stage_invalid(_("Invalid token"))
            token = tokens.first()
            self.executor.plan.context[PLAN_CONTEXT_PENDING_USER] = token.user
            token.delete()
            messages.success(request, _("Successfully verified Email."))
            if self.executor.current_stage.activate_user_on_success:
                self.executor.plan.context[PLAN_CONTEXT_PENDING_USER].is_active = True
                self.executor.plan.context[PLAN_CONTEXT_PENDING_USER].save()
            return self.executor.stage_ok()
        if PLAN_CONTEXT_PENDING_USER not in self.executor.plan.context:
            LOGGER.debug("No pending user")
            messages.error(self.request, _("No pending user."))
            return self.executor.stage_invalid()
        # Check if we've already sent the initial e-mail
        if PLAN_CONTEXT_EMAIL_SENT not in self.executor.plan.context:
            self.send_email()
            self.executor.plan.context[PLAN_CONTEXT_EMAIL_SENT] = True
        return super().get(request, *args, **kwargs)

    def get_challenge(self) -> Challenge:
        challenge = EmailChallenge(
            data={
                "type": ChallengeTypes.NATIVE.value,
                "title": _("Email sent."),
            }
        )
        return challenge

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        return super().challenge_invalid(response)

    def challenge_invalid(self, response: ChallengeResponse) -> HttpResponse:
        if PLAN_CONTEXT_PENDING_USER not in self.executor.plan.context:
            messages.error(self.request, _("No pending user."))
            return super().challenge_invalid(response)
        self.send_email()
        # We can't call stage_ok yet, as we're still waiting
        # for the user to click the link in the email
        return super().challenge_invalid(response)
