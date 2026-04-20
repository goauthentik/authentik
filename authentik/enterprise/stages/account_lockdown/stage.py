"""Account lockdown stage logic"""

from django.db.transaction import atomic
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils.html import escape
from django.utils.translation import gettext_lazy as _

from authentik.core.models import Session, Token, User, UserTypes
from authentik.enterprise.stages.account_lockdown.models import AccountLockdownStage
from authentik.events.models import Event, EventAction
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import StageView
from authentik.flows.views.executor import SESSION_KEY_GET
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT

PLAN_CONTEXT_LOCKDOWN_REASON = "lockdown_reason"
QS_LOCKDOWN_USER = "user_uuid"

TARGET_REQUIRED_MESSAGE = _("No target user specified for account lockdown")
PERMISSION_DENIED_MESSAGE = _("You do not have permission to lock down this account.")
ACCOUNT_LOCKDOWN_FAILED_MESSAGE = _("Account lockdown failed for this account.")
SELF_SERVICE_FAILURE_MESSAGE_TITLE = _("Account lockdown failed")
SELF_SERVICE_FAILURE_MESSAGE = (
    _(
        "<p>We could not lock your account. Please contact your administrator or "
        "security team for assistance.</p>"
    )
)


def render_lockdown_message_html(title: str, body: str) -> str:
    """Render simple lockdown message markup."""
    return f"<h1>{escape(title)}</h1>{body}"


class AccountLockdownStageView(StageView):
    """Execute account lockdown actions on the target user."""

    def get_target_user_uuid(self, request: HttpRequest) -> str | None:
        """Read the requested lockdown target from the flow query parameters."""
        get_params = request.session.get(SESSION_KEY_GET, request.GET)
        return get_params.get(QS_LOCKDOWN_USER)

    def get_target_user(self, request: HttpRequest) -> User | None:
        """Get the target user from the plan context or the authenticated request.

        Priority:
        1. Explicit user_uuid query parameter
        2. PLAN_CONTEXT_PENDING_USER (compatibility fallback)
        3. request.user (direct self-service execution)
        """
        if target_uuid := self.get_target_user_uuid(request):
            return (
                User.objects.exclude_anonymous()
                .exclude(type=UserTypes.INTERNAL_SERVICE_ACCOUNT)
                .filter(pk=target_uuid)
                .first()
            )
        if PLAN_CONTEXT_PENDING_USER in self.executor.plan.context:
            return self.executor.plan.context[PLAN_CONTEXT_PENDING_USER]
        if request.user.is_authenticated:
            return request.user
        return None

    def is_self_service(self, request: HttpRequest, user: User) -> bool:
        """Check whether the currently authenticated user is locking their own account."""
        return request.user.is_authenticated and user.pk == request.user.pk

    def can_lock_target(self, request: HttpRequest, user: User) -> bool:
        """Check whether the requester is allowed to lock the target account."""
        if self.is_self_service(request, user):
            return True
        perm = "authentik_core.change_user"
        return request.user.is_authenticated and (
            request.user.has_perm(perm) or request.user.has_perm(perm, user)
        )

    def get_reason(self) -> str:
        """Get the lockdown reason from the plan context.

        Priority:
        1. prompt_data[PLAN_CONTEXT_LOCKDOWN_REASON]
        2. PLAN_CONTEXT_LOCKDOWN_REASON (explicitly set)
        3. Empty string as fallback
        """
        prompt_data = self.executor.plan.context.get(PLAN_CONTEXT_PROMPT, {})
        if PLAN_CONTEXT_LOCKDOWN_REASON in prompt_data:
            return prompt_data[PLAN_CONTEXT_LOCKDOWN_REASON]
        return self.executor.plan.context.get(PLAN_CONTEXT_LOCKDOWN_REASON, "")

    def _lockdown_user(
        self,
        request: HttpRequest,
        stage: AccountLockdownStage,
        user: User,
        reason: str,
    ) -> None:
        """Execute lockdown actions on a single user."""
        with atomic():
            user = User.objects.select_for_update().get(pk=user.pk)
            if stage.deactivate_user:
                user.is_active = False
            if stage.set_unusable_password:
                user.set_unusable_password()
            user.save()

            if stage.delete_sessions:
                Session.objects.filter(authenticatedsession__user=user).delete()

            if stage.revoke_tokens:
                from authentik.providers.oauth2.models import (
                    AccessToken,
                    AuthorizationCode,
                    DeviceToken,
                    RefreshToken,
                )

                Token.objects.filter(user=user).delete()
                AuthorizationCode.objects.filter(user=user).delete()
                AccessToken.objects.filter(user=user).delete()
                RefreshToken.objects.filter(user=user).delete()
                DeviceToken.objects.filter(user=user).delete()

        # Emit the audit event after the transaction commits. If event creation
        # fails here, dispatch() would otherwise treat the whole lockdown as
        # failed even though the account changes have already been committed.
        try:
            Event.new(
                EventAction.USER_LOCKDOWN_TRIGGERED,
                reason=reason,
                affected_user=user.username,
            ).from_http(request)
        except Exception as exc:  # noqa: BLE001
            # Event emission should not make the lockdown itself fail.
            self.logger.warning(
                "Failed to emit account lockdown event",
                user=user.username,
                exc=exc,
            )

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        """Execute account lockdown actions."""
        stage: AccountLockdownStage = self.executor.current_stage

        user = self.get_target_user(request)
        if not user:
            self.logger.warning("No target user found for account lockdown")
            return self.executor.stage_invalid(TARGET_REQUIRED_MESSAGE)
        if not self.can_lock_target(request, user):
            self.logger.warning(
                "Permission denied for account lockdown",
                actor=getattr(request.user, "username", None),
                target=user.username,
            )
            return self.executor.stage_invalid(PERMISSION_DENIED_MESSAGE)

        reason = self.get_reason()
        self_service = self.is_self_service(request, user)

        self.logger.info(
            "Executing account lockdown",
            user=user.username,
            reason=reason,
            self_service=self_service,
            deactivate_user=stage.deactivate_user,
            set_unusable_password=stage.set_unusable_password,
            delete_sessions=stage.delete_sessions,
            revoke_tokens=stage.revoke_tokens,
        )

        try:
            self._lockdown_user(request, stage, user, reason)
            self.logger.info("Account lockdown completed", user=user.username)
            success = True
        except Exception as exc:  # noqa: BLE001
            self.logger.warning("Account lockdown failed", user=user.username, exc=exc)
            success = False

        failed = not success
        if self_service:
            if failed:
                return self._self_service_message_response(request, stage, success=False)
            if stage.delete_sessions:
                return self._self_service_completion_response(request)
            return self.executor.stage_ok()

        if failed:
            return self.executor.stage_invalid(ACCOUNT_LOCKDOWN_FAILED_MESSAGE)

        return self.executor.stage_ok()

    def _self_service_completion_response(self, request: HttpRequest) -> HttpResponse:
        """Redirect to completion flow after self-service lockdown.

        Since all sessions are deleted, the user cannot continue in the flow.
        Redirect them to an unauthenticated completion flow that shows the
        lockdown message.

        We use a direct HTTP redirect instead of a challenge because the
        flow executor's challenge handling may try to access the session
        which we just deleted.
        """
        stage: AccountLockdownStage = self.executor.current_stage
        completion_flow = stage.self_service_completion_flow
        if completion_flow:
            # Flush the current request's session to prevent Django's session
            # middleware from trying to save a deleted session
            if hasattr(request, "session"):
                request.session.flush()
            redirect_to = reverse(
                "authentik_core:if-flow",
                kwargs={"flow_slug": completion_flow.slug},
            )
            return HttpResponseRedirect(redirect_to)
        return self._self_service_message_response(request, stage, success=True)

    def _self_service_message_response(
        self, request: HttpRequest, stage: AccountLockdownStage, *, success: bool
    ) -> HttpResponse:
        """Return a message response for self-service lockdowns."""
        if stage.delete_sessions and hasattr(request, "session"):
            request.session.flush()
        if success:
            title = stage.self_service_message_title
            body = stage.self_service_message
        else:
            title = SELF_SERVICE_FAILURE_MESSAGE_TITLE
            body = SELF_SERVICE_FAILURE_MESSAGE
        return HttpResponse(render_lockdown_message_html(title, body))
