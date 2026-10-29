"""Email Setup stage"""

from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.http.request import QueryDict
from django.template.exceptions import TemplateSyntaxError
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework.fields import BooleanField, CharField

from authentik.events.models import Event, EventAction
from authentik.flows.challenge import (
    Challenge,
    ChallengeResponse,
    WithUserInfoChallenge,
)
from authentik.flows.exceptions import StageInvalidException
from authentik.flows.stage import ChallengeStageView
from authentik.lib.utils.email import mask_email
from authentik.lib.utils.time import timedelta_from_string
from authentik.stages.authenticator_email.models import (
    AuthenticatorEmailStage,
    EmailDevice,
)
from authentik.stages.email.tasks import send_mails
from authentik.stages.email.throttling import email_is_rate_limited
from authentik.stages.email.utils import TemplateEmailMessage
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT

PLAN_CONTEXT_EMAIL_DEVICE = "goauthentik.io/stages/authenticator_email/email_device"
PLAN_CONTEXT_EMAIL_SEND_ERROR = "goauthentik.io/stages/authenticator_email/send_error"
PLAN_CONTEXT_EMAIL = "email"
PLAN_CONTEXT_EMAIL_SENT = "email_sent"
PLAN_CONTEXT_EMAIL_OVERRIDE = "email"


class AuthenticatorEmailChallenge(WithUserInfoChallenge):
    """Authenticator Email Setup challenge"""

    # Set to true if no previous prompt stage set the email
    # this stage will also check prompt_data.email
    email = CharField(default=None, allow_blank=True, allow_null=True)
    email_required = BooleanField(default=True)
    component = CharField(default="ak-stage-authenticator-email")


class AuthenticatorEmailChallengeResponse(ChallengeResponse):
    """Authenticator Email Challenge response, device is set by get_response_instance"""

    device: EmailDevice

    code = CharField(required=False)
    email = CharField(required=False)

    component = CharField(default="ak-stage-authenticator-email")

    def validate(self, attrs: dict) -> dict:
        """Check"""
        if "code" not in attrs:
            # Keep the destination established by the flow, even if the request
            # supplies a different address.
            email = self.stage._has_email()
            if email is None:
                if "email" not in attrs:
                    raise ValidationError("email required")
                email = attrs["email"]
            if self.device.email == email:
                self.stage.resend()
            else:
                self.stage.validate_and_send(email)
                self.device.email = email
            return super().validate(attrs)
        if not self.device.verify_token(str(attrs["code"])):
            raise ValidationError(_("Code does not match"))
        self.device.confirmed = True
        return super().validate(attrs)


class AuthenticatorEmailStageView(ChallengeStageView):
    """Authenticator Email Setup stage"""

    response_class = AuthenticatorEmailChallengeResponse

    def validate_and_send(self, email: str):
        """Validate email and send message using the shared email attempt limit."""
        stage: AuthenticatorEmailStage = self.executor.current_stage
        if EmailDevice.objects.filter(Q(email=email), stage=stage.pk).exists():
            raise ValidationError(_("Invalid email"))

        self._check_rate_limit(email)
        self._send_email(email)

    def _check_rate_limit(self, email: str):
        if minutes_left := email_is_rate_limited(email):
            raise ValidationError(
                _(
                    "Too many account verification attempts. "
                    "Please try again after {minutes} minutes."
                ).format(minutes=minutes_left),
                code="throttled",
            )

    def _send_email(self, email: str):
        pending_user = self.get_pending_user()
        stage: AuthenticatorEmailStage = self.executor.current_stage
        device: EmailDevice = self.executor.plan.context[PLAN_CONTEXT_EMAIL_DEVICE]
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
            self.executor.plan.context.pop(PLAN_CONTEXT_EMAIL_SEND_ERROR, None)
        except TemplateSyntaxError as exc:
            Event.new(
                EventAction.CONFIGURATION_ERROR,
                message=_("Exception occurred while rendering E-mail template"),
                template=stage.template,
            ).with_exception(exc).from_http(self.request)
            raise StageInvalidException from exc

    def resend(self):
        """Regenerate the token and re-send it to the device's existing email address."""
        device: EmailDevice = self.executor.plan.context[PLAN_CONTEXT_EMAIL_DEVICE]
        stage: AuthenticatorEmailStage = self.executor.current_stage
        self._check_rate_limit(device.email)
        valid_secs: int = timedelta_from_string(stage.token_expiry).total_seconds()
        device.generate_token(valid_secs=valid_secs, commit=False)
        self._send_email(device.email)

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
        if PLAN_CONTEXT_EMAIL_DEVICE in self.executor.plan.context:
            self.logger.debug("got email from device in session")
            device: EmailDevice = self.executor.plan.context[PLAN_CONTEXT_EMAIL_DEVICE]
            if device.email == "":
                return None
            return device.email
        return None

    def get_challenge(self, *args, **kwargs) -> Challenge:
        email = self._has_email()
        data = {"email": mask_email(email), "email_required": email is None}
        if send_error := self.executor.plan.context.get(PLAN_CONTEXT_EMAIL_SEND_ERROR):
            data["response_errors"] = send_error
        return AuthenticatorEmailChallenge(data=data)

    def get_response_instance(self, data: QueryDict) -> ChallengeResponse:
        response = super().get_response_instance(data)
        response.device = self.executor.plan.context[PLAN_CONTEXT_EMAIL_DEVICE]
        return response

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        user = self.get_pending_user()

        # An unsaved pending user (e.g. denied by a policy before being created, such as a
        # disallowed email domain) has no primary key. Using it in a related-field filter below
        # raises "Model instances passed to related filters must be saved" and 500s the flow.
        # Such a user must not proceed anyway, so deny cleanly instead of crashing.
        if not user.pk:
            return self.executor.stage_invalid(_("Access denied."))

        stage: AuthenticatorEmailStage = self.executor.current_stage
        # For the moment we only allow one email device per user
        if EmailDevice.objects.filter(Q(user=user), stage=stage.pk).exists():
            return self.executor.stage_invalid(
                _("The user already has an email address registered for MFA.")
            )
        if PLAN_CONTEXT_EMAIL_DEVICE not in self.executor.plan.context:
            self.executor.plan.context.pop(PLAN_CONTEXT_EMAIL_SEND_ERROR, None)
            device = EmailDevice(user=user, confirmed=False, stage=stage, name="Email Device")
            valid_secs: int = timedelta_from_string(stage.token_expiry).total_seconds()
            device.generate_token(valid_secs=valid_secs, commit=False)
            self.executor.plan.context[PLAN_CONTEXT_EMAIL_DEVICE] = device
            if email := self._has_email():
                device.email = email
                try:
                    self.validate_and_send(email)
                except ValidationError as exc:
                    if exc.get_codes() == ["throttled"]:
                        self.executor.plan.context[PLAN_CONTEXT_EMAIL_SEND_ERROR] = {
                            "non_field_errors": [
                                {
                                    "string": str(
                                        _(
                                            "Email sending was rate limited. "
                                            "Request a new code to try again."
                                        )
                                    ),
                                    "code": "throttled",
                                }
                            ]
                        }
                        return super().get(request, *args, **kwargs)
                    # We had an email given already (at this point only possible from flow
                    # context), but an error occurred while sending (most likely)
                    # due to a duplicate device, so delete the email we got given, reset the state
                    # (ish) and retry
                    device.email = ""
                    self.executor.plan.context.get(PLAN_CONTEXT_PROMPT, {}).pop(
                        PLAN_CONTEXT_EMAIL, None
                    )
                    self.executor.plan.context.pop(PLAN_CONTEXT_EMAIL_DEVICE, None)
                    self.logger.warning("failed to send email to pre-set address", exc=exc)
                    return self.get(request, *args, **kwargs)
        return super().get(request, *args, **kwargs)

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        """Email Token is validated by challenge"""
        device: EmailDevice = self.executor.plan.context[PLAN_CONTEXT_EMAIL_DEVICE]
        if not device.confirmed:
            return self.challenge_invalid(response)
        device.save()
        del self.executor.plan.context[PLAN_CONTEXT_EMAIL_DEVICE]
        return self.executor.stage_ok()
