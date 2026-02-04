"""Account lockdown stage logic"""

from django.db.transaction import atomic
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils.html import escape
from django.utils.translation import gettext as _

from authentik.core.models import Session, Token, User
from authentik.enterprise.stages.account_lockdown.models import (
    PLAN_CONTEXT_LOCKDOWN_REASON,
    PLAN_CONTEXT_LOCKDOWN_RESULTS,
    PLAN_CONTEXT_LOCKDOWN_SELF_SERVICE,
    PLAN_CONTEXT_LOCKDOWN_TARGET,
    PLAN_CONTEXT_LOCKDOWN_TARGETS,
    AccountLockdownStage,
)
from authentik.events.models import Event, EventAction
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import StageView
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT


class AccountLockdownStageView(StageView):
    """Execute account lockdown actions on target user(s)."""

    def get_target_users(self) -> list[User]:
        """Get target user(s) from the plan context.

        Priority:
        1. PLAN_CONTEXT_LOCKDOWN_TARGETS (list of users for bulk lockdown)
        2. PLAN_CONTEXT_LOCKDOWN_TARGET (explicitly set single target)
        3. PLAN_CONTEXT_PENDING_USER (user being processed in flow)
        """
        # Check for multiple users first (bulk)
        if PLAN_CONTEXT_LOCKDOWN_TARGETS in self.executor.plan.context:
            return self.executor.plan.context[PLAN_CONTEXT_LOCKDOWN_TARGETS]
        # Single user
        if PLAN_CONTEXT_LOCKDOWN_TARGET in self.executor.plan.context:
            return [self.executor.plan.context[PLAN_CONTEXT_LOCKDOWN_TARGET]]
        if PLAN_CONTEXT_PENDING_USER in self.executor.plan.context:
            return [self.executor.plan.context[PLAN_CONTEXT_PENDING_USER]]
        return []

    def get_reason(self) -> str:
        """Get the lockdown reason from the plan context.

        Priority:
        1. prompt_data['reason'] (from a prompt stage)
        2. PLAN_CONTEXT_LOCKDOWN_REASON (explicitly set)
        3. Empty string as fallback
        """
        prompt_data = self.executor.plan.context.get(PLAN_CONTEXT_PROMPT, {})
        if "reason" in prompt_data:
            return prompt_data["reason"]
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
            if stage.deactivate_user:
                user.is_active = False
            if stage.set_unusable_password:
                user.set_unusable_password()
            user.save()

            if stage.delete_sessions:
                Session.objects.filter(authenticatedsession__user=user).delete()

            if stage.revoke_tokens:
                Token.objects.filter(user=user).delete()

        # Create event outside atomic block - lockdown succeeded, now log it
        # This ensures the lockdown happens even if event creation fails
        try:
            Event.new(
                EventAction.ACCOUNT_LOCKDOWN_TRIGGERED,
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

        users = self.get_target_users()
        if not users:
            self.logger.warning("No target user found for account lockdown")
            return self.executor.stage_invalid("No target user specified for account lockdown")

        reason = self.get_reason()
        self_service = self.executor.plan.context.get(PLAN_CONTEXT_LOCKDOWN_SELF_SERVICE, False)

        # Track results for each user
        results = []

        for user in users:
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
                results.append({"user": user, "success": True, "error": None})
            except Exception as exc:  # noqa: BLE001
                self.logger.warning("Account lockdown failed", user=user.username, exc=exc)
                results.append({"user": user, "success": False, "error": str(exc)})

        # Store results in plan context for completion stage
        self.executor.plan.context[PLAN_CONTEXT_LOCKDOWN_RESULTS] = results

        if self_service:
            any_failed = any(not result["success"] for result in results)
            if any_failed:
                return self._self_service_message_response(request, stage, success=False)
            if stage.delete_sessions:
                return self._self_service_completion_response(request)
            return self.executor.stage_ok()

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
            title = _("Account lockdown failed")
            body = _(
                "<p>We could not lock your account. Please contact your administrator or "
                "security team for assistance.</p>"
            )
        html = f"<h1>{escape(title)}</h1>{body}"
        return HttpResponse(html)
