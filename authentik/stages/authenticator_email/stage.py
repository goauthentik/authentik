"""Email Setup stage"""

from time import time

from django.core.cache import cache
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
from authentik.stages.email.utils import TemplateEmailMessage
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT

PLAN_CONTEXT_EMAIL_DEVICE = "goauthentik.io/stages/authenticator_email/email_device"
PLAN_CONTEXT_EMAIL = "email"
PLAN_CONTEXT_EMAIL_SENT = "email_sent"
PLAN_CONTEXT_EMAIL_OVERRIDE = "email"

# Minimum interval between two sign-in codes sent to the same address. Enforced server-side so a
# client that skips the UI countdown cannot use the resend endpoint to mail-bomb an address. Keyed
# by address rather than by session, otherwise starting a fresh flow would reset the limit.
RESEND_THROTTLE_SECONDS = 60
RESEND_THROTTLE_KEY = "goauthentik.io/stages/authenticator_email/resend_throttle/%s"


def _throttle_key(email: str) -> str:
    return RESEND_THROTTLE_KEY % email.lower()


def resend_cooldown_remaining(email: str) -> int:
    """Read-only: seconds left before another code may be sent to `email` (for UI messages)."""
    if not email:
        return 0
    ready_at = cache.get(_throttle_key(email))
    if not ready_at:
        return 0
    return max(int(ready_at - time()), 0)


def reserve_send(email: str) -> int:
    """Atomically claim the right to send a code to `email`.

    Returns 0 when the caller may send now (the window was opened for it), otherwise the number of
    seconds until the next send is allowed. cache.add (Redis SETNX) makes this race-free: with a
    burst of concurrent send requests only the first one gets 0, the rest are refused.

    The caller must send the code once it gets 0, or call release_send() if the send fails, so a
    failed attempt does not lock the address out for the full window.
    """
    if not email:
        return 0
    deadline = time() + RESEND_THROTTLE_SECONDS
    if cache.add(_throttle_key(email), deadline, timeout=RESEND_THROTTLE_SECONDS):
        return 0
    return resend_cooldown_remaining(email)


def release_send(email: str) -> None:
    """Release a window reserved by reserve_send() when the send did not actually go out."""
    if not email:
        return
    cache.delete(_throttle_key(email))


def throttled_error(remaining: int) -> ValidationError:
    """User-facing error for a resend attempt made during the cooldown window."""
    return ValidationError(
        _("A code was just sent. You can request a new one in %(seconds)d seconds.")
        % {"seconds": remaining}
    )


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
            if "email" not in attrs:
                # No code and no email on the OTP entry screen (device email already set):
                # treat as a "resend" request — regenerate the token and email it again.
                if self.device.email:
                    # Reserve before regenerating the token, so a throttled attempt leaves the
                    # code already in the user's inbox untouched.
                    remaining = reserve_send(self.device.email)
                    if remaining:
                        raise throttled_error(remaining)
                    self.stage.resend()
                    return super().validate(attrs)
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

    def validate_and_send(self, email: str, reserve: bool = True):
        """Validate email and send message.

        `reserve` gates this send through the per-address cooldown; the resend path passes
        reserve=False because it already reserved the window before regenerating the token.
        """
        # Throttle every direct send too (initial entry / re-submitting the email challenge),
        # otherwise the resend cooldown could be bypassed by replaying the email step.
        if reserve:
            remaining = reserve_send(email)
            if remaining:
                raise throttled_error(remaining)

        pending_user = self.get_pending_user()

        stage: AuthenticatorEmailStage = self.executor.current_stage
        if EmailDevice.objects.filter(Q(email=email), stage=stage.pk).exists():
            release_send(email)
            raise ValidationError(_("Invalid email"))

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
        except TemplateSyntaxError as exc:
            release_send(email)
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
        valid_secs: int = timedelta_from_string(stage.token_expiry).total_seconds()
        device.generate_token(valid_secs=valid_secs, commit=False)
        # The resend branch already reserved the cooldown window before this token was regenerated.
        self.validate_and_send(device.email, reserve=False)

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
        return AuthenticatorEmailChallenge(
            data={
                "email": mask_email(email),
                "email_required": email is None,
            }
        )

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
            device = EmailDevice(user=user, confirmed=False, stage=stage, name="Email Device")
            valid_secs: int = timedelta_from_string(stage.token_expiry).total_seconds()
            device.generate_token(valid_secs=valid_secs, commit=False)
            self.executor.plan.context[PLAN_CONTEXT_EMAIL_DEVICE] = device
            if email := self._has_email():
                device.email = email
                try:
                    # This auto-send runs once per flow plan (guarded above), so it is not an
                    # attacker-repeatable path; skip the cooldown gate to avoid the retry loop
                    # below spinning on a throttle error.
                    self.validate_and_send(email, reserve=False)
                except ValidationError as exc:
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
