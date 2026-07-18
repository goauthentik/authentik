"""authentik multi-stage authentication engine"""

import math
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from uuid import uuid4

from django.contrib import messages
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse
from django.http.request import QueryDict
from django.template.exceptions import TemplateSyntaxError
from django.urls import reverse
from django.utils.text import slugify
from django.utils.timezone import now
from django.utils.translation import gettext as _
from rest_framework.fields import CharField
from rest_framework.serializers import ValidationError

from authentik.events.models import Event, EventAction
from authentik.flows.challenge import Challenge, ChallengeResponse
from authentik.flows.exceptions import StageInvalidException
from authentik.flows.models import FlowDesignation, FlowToken
from authentik.flows.planner import PLAN_CONTEXT_IS_RESTORED, PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import ChallengeStageView
from authentik.flows.views.executor import QS_KEY_TOKEN, QS_QUERY
from authentik.lib.utils.time import timedelta_from_string
from authentik.stages.email.flow import pickle_flow_token_for_email
from authentik.stages.email.models import EmailStage
from authentik.stages.email.tasks import send_mails
from authentik.stages.email.utils import TemplateEmailMessage

EMAIL_RECOVERY_CACHE_KEY = "goauthentik.io/stages/email/stage/"

PLAN_CONTEXT_EMAIL_SENT = "email_sent"
PLAN_CONTEXT_EMAIL_OVERRIDE = "email"


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
        # Parse query string from current URL (full query string)
        # this view is only run within a flow executor, where we need to get the query string
        # from the query= parameter (double encoded); but for the redirect
        # we need to expand it since it'll go through the flow interface
        query_params = QueryDict(self.request.GET.get(QS_QUERY), mutable=True)
        query_params.pop(QS_KEY_TOKEN, None)
        query_params.update(kwargs)
        full_url = base_url
        if len(query_params) > 0:
            full_url = f"{full_url}?{query_params.urlencode()}"
        return self.request.build_absolute_uri(full_url)

    def get_token(self) -> FlowToken:
        """Get token"""
        pending_user = self.get_pending_user()
        current_stage: EmailStage = self.executor.current_stage
        valid_delta = timedelta_from_string(current_stage.token_expiry) + timedelta(
            minutes=1
        )  # + 1 because django timesince always rounds down
        identifier = slugify(f"ak-email-stage-{current_stage.name}-{str(uuid4())}")
        # Don't check for validity here, we only care if the token exists
        tokens = FlowToken.objects.filter(identifier=identifier)
        if not tokens.exists():
            return FlowToken.objects.create(
                expires=now() + valid_delta,
                user=pending_user,
                identifier=identifier,
                flow=self.executor.flow,
                _plan=pickle_flow_token_for_email(self.executor.plan),
                revoke_on_execution=False,
            )
        token = tokens.first()
        # Check if token is expired and rotate key if so
        if token.is_expired:
            token.expire_action()
        return token

    def send_email(self):
        """Helper function that sends the actual email. Implies that you've
        already checked that there is a pending user."""
        pending_user = self.get_pending_user()
        if not pending_user.pk and self.executor.flow.designation == FlowDesignation.RECOVERY:
            # Pending user does not have a primary key, and we're in a recovery flow,
            # which means the user entered an invalid identifier, so we pretend to send the
            # email, to not disclose if the user exists
            return
        email = self.executor.plan.context.get(PLAN_CONTEXT_EMAIL_OVERRIDE, None)
        if not email:
            email = pending_user.email
        current_stage: EmailStage = self.executor.current_stage
        token = self.get_token()
        # Send mail to user
        try:
            message = TemplateEmailMessage(
                subject=_(current_stage.subject),
                to=[(pending_user.name, email)],
                language=pending_user.locale(self.request),
                template_name=current_stage.template,
                template_context={
                    "url": self.get_full_url(**{QS_KEY_TOKEN: token.key}),
                    "user": pending_user,
                    "expires": token.expires,
                    "token": token.key,
                },
            )
            send_mails(current_stage, message)
        except TemplateSyntaxError as exc:
            Event.new(
                EventAction.CONFIGURATION_ERROR,
                message=_("Exception occurred while rendering E-mail template"),
                template=current_stage.template,
            ).with_exception(exc).from_http(self.request)
            raise StageInvalidException from exc

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        # Check if the user came back from the email link to verify
        restore_token: FlowToken = self.executor.plan.context.get(PLAN_CONTEXT_IS_RESTORED, None)
        user = self.get_pending_user()
        if restore_token:
            if restore_token.user != user:
                self.logger.warning("Flow token for non-matching user, denying request")
                return self.executor.stage_invalid()
            messages.success(request, _("Successfully verified Email."))
            if self.executor.current_stage.activate_user_on_success:
                user.is_active = True
                user.save(update_fields=["is_active"])
            return self.executor.stage_ok()
        if PLAN_CONTEXT_PENDING_USER not in self.executor.plan.context:
            self.logger.debug("No pending user")
            messages.error(self.request, _("No pending user."))
            return self.executor.stage_invalid()
        # Check if we've already sent the initial e-mail
        if PLAN_CONTEXT_EMAIL_SENT not in self.executor.plan.context:
            try:
                self.send_email()
            except StageInvalidException as exc:
                self.logger.debug("Got StageInvalidException", exc=exc)
                return self.executor.stage_invalid()
            self.executor.plan.context[PLAN_CONTEXT_EMAIL_SENT] = True
        return super().get(request, *args, **kwargs)

    def get_challenge(self) -> Challenge:
        challenge = EmailChallenge(
            data={
                "title": _("Email sent."),
            }
        )
        return challenge

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        return super().challenge_invalid(response)

    def _get_cache_key(self) -> str:
        """Return the cache key used for rate limiting email recovery attempts."""
        user = self.get_pending_user()
        user_email_hashed = sha256(user.email.lower().encode("utf-8")).hexdigest()
        return EMAIL_RECOVERY_CACHE_KEY + user_email_hashed

    def _is_rate_limited(self) -> int | None:
        """Check whether the email recovery attempt should be rate limited.

        If the request should be rate limited, update the cache and return the
        remaining time in minutes before the user is allowed to try again.
        Otherwise, return None."""
        cache_key = self._get_cache_key()
        attempts = cache.get(cache_key, [])

        stage = self.executor.current_stage
        stage.refresh_from_db()
        max_attempts = stage.recovery_max_attempts
        cache_timeout_delta = timedelta_from_string(stage.recovery_cache_timeout)

        _now = now()
        start_window = _now - cache_timeout_delta

        # Convert unix timestamps to datetime objects for comparison
        recent_attempts_in_window = [
            datetime.fromtimestamp(attempt, UTC)
            for attempt in attempts
            if datetime.fromtimestamp(attempt, UTC) > start_window
        ]

        if len(recent_attempts_in_window) >= max_attempts:
            retry_after = (min(recent_attempts_in_window) + cache_timeout_delta) - _now
            minutes_left = max(1, math.ceil(retry_after.total_seconds() / 60))
            return minutes_left

        recent_attempts_in_window.append(_now)

        # Convert datetime objects back to unix timestamps to update cache
        recent_attempts_in_window = [attempt.timestamp() for attempt in recent_attempts_in_window]

        cache.set(
            cache_key,
            recent_attempts_in_window,
            int(cache_timeout_delta.total_seconds()),
        )

        return None

    def challenge_invalid(self, response: ChallengeResponse) -> HttpResponse:
        if minutes_left := self._is_rate_limited():
            error = _(
                "Too many account verification attempts. Please try again after {minutes} minutes."
            ).format(minutes=minutes_left)
            messages.error(self.request, error)
            return super().challenge_invalid(response)

        if PLAN_CONTEXT_PENDING_USER not in self.executor.plan.context:
            messages.error(self.request, _("No pending user."))
            return super().challenge_invalid(response)

        self.send_email()
        messages.success(self.request, _("Email Successfully sent."))
        # We can't call stage_ok yet, as we're still waiting
        # for the user to click the link in the email
        return super().challenge_invalid(response)
