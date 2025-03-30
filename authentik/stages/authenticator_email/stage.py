"""Email Setup stage"""

from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.http.request import QueryDict
from django.template.exceptions import TemplateSyntaxError
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework.fields import BooleanField, CharField, IntegerField

from authentik.events.models import Event, EventAction
from authentik.flows.challenge import (
    Challenge,
    ChallengeResponse,
    WithUserInfoChallengeMixin,
)
from authentik.flows.exceptions import StageInvalidException
from authentik.flows.stage import ChallengeStageView
from authentik.lib.utils.email import mask_email
from authentik.lib.utils.errors import exception_to_string
from authentik.lib.utils.time import timedelta_from_string
from authentik.stages.authenticator_email.models import (
    AuthenticatorEmailStage,
    EmailDevice,
)
from authentik.stages.email.tasks import send_mails
from authentik.stages.email.utils import TemplateEmailMessage
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT

SESSION_KEY_EMAIL_DEVICE = "authentik/stages/authenticator_email/email_device"
PLAN_CONTEXT_EMAIL = "email"
PLAN_CONTEXT_EMAIL_SENT = "email_sent"
PLAN_CONTEXT_EMAIL_OVERRIDE = "email"


class AuthenticatorEmailChallenge(WithUserInfoChallengeMixin, Challenge):
    """Authenticator Email Setup challenge"""

    # Set to true if no previous prompt stage set the email
    # this stage will also check prompt_data.email
    email = CharField(default=None, allow_blank=True, allow_null=True)
    email_required = BooleanField(default=True)
    component = CharField(default="ak-stage-authenticator-email")


class AuthenticatorEmailChallengeResponse(ChallengeResponse):
    """Authenticator Email Challenge response, device is set by get_response_instance"""

    device: EmailDevice

    code = IntegerField(required=False)
    email = CharField(required=False)

    component = CharField(default="ak-stage-authenticator-email")

    def validate(self, attrs: dict) -> dict:
        """Check"""
        if "code" not in attrs:
            if "email" not in attrs:
                raise ValidationError("email required")
            self.device.email = attrs["email"]
            self.stage.validate_and_send(attrs["email"])
            return super().validate(attrs)
        if not self.device.verify_token(str(attrs["code"])):
            raise ValidationError(_("Code does not match"))
        self.device.confirmed = True
        return super().validate(attrs)


class AuthenticatorEmailStageView(ChallengeStageView):
    """Authenticator Email Setup stage"""

    response_class = AuthenticatorEmailChallengeResponse

    def validate_and_send(self, email: str):
        """Validate email and send message"""
        pending_user = self.get_pending_user()

        stage: AuthenticatorEmailStage = self.executor.current_stage
        if EmailDevice.objects.filter(Q(email=email), stage=stage.pk).exists():
            raise ValidationError(_("Invalid email"))

        device: EmailDevice = self.request.session[SESSION_KEY_EMAIL_DEVICE]

        try:
            message = TemplateEmailMessage(
                subject=_(stage.subject),
                to=[(pending_user.name, email)],
                language=pending_user.locale(self.request),
                template_name=stage.template,
                template_context={
                    "user": pending_user,
                    "expires": device.valid_until,
                    "token": device.token,
                },
            )

            send_mails(stage, message)
        except TemplateSyntaxError as exc:
            Event.new(
                EventAction.CONFIGURATION_ERROR,
                message=_("Exception occurred while rendering E-mail template"),
                error=exception_to_string(exc),
                template=stage.template,
            ).from_http(self.request)
            raise StageInvalidException from exc

    def _has_email(self) -> str | None:
        context = self.executor.plan.context

        # Check user's email attribute
        user = self.get_pending_user()
        if user.email:
            self.logger.debug("got email from user attributes")
            return user.email
        # Check plan context for email
        if PLAN_CONTEXT_EMAIL in context.get(PLAN_CONTEXT_PROMPT, {}):
            self.logger.debug("got email from plan context")
            return context.get(PLAN_CONTEXT_PROMPT, {}).get(PLAN_CONTEXT_EMAIL)
        # Check device for email
        if SESSION_KEY_EMAIL_DEVICE in self.request.session:
            self.logger.debug("got email from device in session")
            device: EmailDevice = self.request.session[SESSION_KEY_EMAIL_DEVICE]
            if device.email == "":
                return None
            return device.email
        return None

    def get_challenge(self, *args, **kwargs) -> Challenge:
        email = self._has_email()
        return AuthenticatorEmailChallenge(
            data={
                "email": mask_email(email),
                "email_required": email is None,
            }
        )

    def get_response_instance(self, data: QueryDict) -> ChallengeResponse:
        response = super().get_response_instance(data)
        response.device = self.request.session[SESSION_KEY_EMAIL_DEVICE]
        return response

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        user = self.get_pending_user()

        stage: AuthenticatorEmailStage = self.executor.current_stage
        if SESSION_KEY_EMAIL_DEVICE not in self.request.session:
            device = EmailDevice(user=user, confirmed=False, stage=stage, name="Email Device")
            valid_secs: int = timedelta_from_string(stage.token_expiry).total_seconds()
            device.generate_token(valid_secs=valid_secs, commit=False)
            self.request.session[SESSION_KEY_EMAIL_DEVICE] = device
            if email := self._has_email():
                device.email = email
                try:
                    self.validate_and_send(email)
                except ValidationError as exc:
                    # We had an email given already (at this point only possible from flow
                    # context), but an error occurred while sending (most likely)
                    # due to a duplicate device, so delete the email we got given, reset the state
                    # (ish) and retry
                    device.email = ""
                    self.executor.plan.context.get(PLAN_CONTEXT_PROMPT, {}).pop(
                        PLAN_CONTEXT_EMAIL, None
                    )
                    self.request.session.pop(SESSION_KEY_EMAIL_DEVICE, None)
                    self.logger.warning("failed to send email to pre-set address", exc=exc)
                    return self.get(request, *args, **kwargs)
        return super().get(request, *args, **kwargs)

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        """Email Token is validated by challenge"""
        device: EmailDevice = self.request.session[SESSION_KEY_EMAIL_DEVICE]
        if not device.confirmed:
            return self.challenge_invalid(response)
        device.save()
        del self.request.session[SESSION_KEY_EMAIL_DEVICE]
        return self.executor.stage_ok()
