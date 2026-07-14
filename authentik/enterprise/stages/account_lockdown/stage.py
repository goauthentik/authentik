"""Account lockdown stage logic"""

from django.apps import apps
from django.core.exceptions import FieldDoesNotExist
from django.db.models import Model, QuerySet
from django.db.models.query_utils import Q
from django.db.transaction import atomic
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from dramatiq.actor import Actor
from dramatiq.composition import group
from dramatiq.results.errors import ResultTimeout

from authentik.core.models import (
    AuthenticatedSession,
    ExpiringModel,
    Session,
    Token,
    User,
    UserTypes,
)
from authentik.enterprise.stages.account_lockdown.models import AccountLockdownStage
from authentik.events.models import Event, EventAction
from authentik.flows.stage import StageView
from authentik.lib.sync.outgoing.models import OutgoingSyncProvider
from authentik.lib.sync.outgoing.signals import sync_outgoing_inhibit_dispatch
from authentik.lib.utils.reflection import class_to_path
from authentik.lib.utils.time import timedelta_from_string
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT

PLAN_CONTEXT_LOCKDOWN_REASON = "lockdown_reason"
LOCKDOWN_EVENT_ACTION_ID = "account_lockdown"

TARGET_REQUIRED_MESSAGE = _("No target user specified for account lockdown")
PERMISSION_DENIED_MESSAGE = _("You do not have permission to lock down this account.")
ACCOUNT_LOCKDOWN_FAILED_MESSAGE = _("Account lockdown failed for this account.")
SELF_SERVICE_COMPLETION_FLOW_REQUIRED_MESSAGE = _(
    "Self-service account lockdown requires a completion flow."
)


def get_lockdown_target_users() -> QuerySet[User]:
    """Return users that can be targeted by account lockdown."""
    return User.objects.exclude_anonymous().exclude(type=UserTypes.INTERNAL_SERVICE_ACCOUNT)


def _get_model_field(model: type[Model], field_name: str):
    """Get a model field by name, if present."""
    try:
        return model._meta.get_field(field_name)
    except FieldDoesNotExist:
        return None


def _has_user_field(model: type[Model]) -> bool:
    """Check if a model has a direct user foreign key."""
    field = _get_model_field(model, "user")
    return bool(field and getattr(field, "remote_field", None) and field.remote_field.model is User)


def _has_authenticated_session_field(model: type[Model]) -> bool:
    """Check if a model is linked to an authenticated session."""
    field = _get_model_field(model, "session")
    return bool(
        field
        and getattr(field, "remote_field", None)
        and field.remote_field.model is AuthenticatedSession
    )


def _has_provider_field(model: type[Model]) -> bool:
    """Check if a model is linked to a provider."""
    return _get_model_field(model, "provider") is not None


def get_lockdown_token_models() -> tuple[type[Model], ...]:
    """Return token, grant, and provider session models removed by account lockdown."""
    token_models: list[type[Model]] = []
    for model in apps.get_models():
        if model._meta.abstract or not issubclass(model, ExpiringModel):
            continue
        if model is Token:
            token_models.append(model)
        elif _has_user_field(model) and (
            _has_provider_field(model) or _has_authenticated_session_field(model)
        ):
            token_models.append(model)
        elif _has_authenticated_session_field(model):
            token_models.append(model)
    return tuple(token_models)


def get_lockdown_token_queryset(model: type[Model], user: User) -> QuerySet:
    """Return account lockdown artifacts for a model and user."""
    manager = model.objects.including_expired()
    if _has_user_field(model):
        return manager.filter(user=user)
    return manager.filter(session__user=user)


def can_lock_user(actor, user: User) -> bool:
    """Check whether the actor may lock the target user."""
    if not actor.is_authenticated:
        return False
    if user.pk == actor.pk:
        return True
    return actor.has_perm("authentik_core.change_user", user)


def get_outgoing_sync_tasks() -> tuple[tuple[type[OutgoingSyncProvider], Actor], ...]:
    """Return outgoing sync provider types and their direct sync tasks."""
    from authentik.enterprise.providers.google_workspace.models import GoogleWorkspaceProvider
    from authentik.enterprise.providers.google_workspace.tasks import google_workspace_sync_direct
    from authentik.enterprise.providers.microsoft_entra.models import MicrosoftEntraProvider
    from authentik.enterprise.providers.microsoft_entra.tasks import microsoft_entra_sync_direct
    from authentik.providers.scim.models import SCIMProvider
    from authentik.providers.scim.tasks import scim_sync_direct

    return (
        (SCIMProvider, scim_sync_direct),
        (GoogleWorkspaceProvider, google_workspace_sync_direct),
        (MicrosoftEntraProvider, microsoft_entra_sync_direct),
    )


class AccountLockdownStageView(StageView):
    """Execute account lockdown actions on the target user."""

    def is_self_service(self, request: HttpRequest, user: User) -> bool:
        """Check whether the currently authenticated user is locking their own account."""
        return request.user.is_authenticated and user.pk == request.user.pk

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

    def _apply_lockdown_actions(self, stage: AccountLockdownStage, user: User) -> None:
        """Apply the configured account changes to the target user."""
        if stage.deactivate_user:
            user.is_active = False
        if stage.set_unusable_password:
            user.set_unusable_password()
        if stage.deactivate_user:
            with sync_outgoing_inhibit_dispatch():
                user.save()
            return
        user.save()

    def _sync_deactivated_user_to_outgoing_providers(self, user: User) -> None:
        """Synchronize a deactivated user to outgoing sync providers."""
        messages = []
        wait_timeout = 0
        model = class_to_path(User)
        provider_filter = Q(backchannel_application__isnull=False) | Q(application__isnull=False)

        for provider_model, task_sync_direct in get_outgoing_sync_tasks():
            for provider in provider_model.objects.filter(provider_filter):
                time_limit = int(
                    timedelta_from_string(provider.sync_page_timeout).total_seconds() * 1000
                )
                messages.append(
                    task_sync_direct.message_with_options(
                        args=(model, user.pk, provider.pk),
                        rel_obj=provider,
                        time_limit=time_limit,
                        uid=f"{provider.name}:user:{user.pk}:direct",
                    )
                )
                wait_timeout += time_limit

        if not messages:
            return
        try:
            group(messages).run().wait(timeout=wait_timeout)
        except ResultTimeout:
            self.logger.warning(
                "Timed out waiting for outgoing sync tasks; tasks remain queued",
                user=user.username,
                timeout=wait_timeout,
            )

    def _get_lockdown_artifact_querysets(
        self, stage: AccountLockdownStage, user: User
    ) -> tuple[QuerySet, ...]:
        """Return the configured sessions and tokens targeted by lockdown."""
        querysets: list[QuerySet] = []
        if stage.delete_sessions:
            querysets.append(Session.objects.filter(authenticatedsession__user=user))
        if stage.revoke_tokens:
            querysets.extend(
                get_lockdown_token_queryset(model, user) for model in get_lockdown_token_models()
            )
        return tuple(querysets)

    def _delete_lockdown_artifacts(self, stage: AccountLockdownStage, user: User) -> None:
        """Delete sessions and tokens selected by the lockdown configuration."""
        for queryset in self._get_lockdown_artifact_querysets(stage, user):
            queryset.delete()

    def _has_lockdown_artifacts(self, stage: AccountLockdownStage, user: User) -> bool:
        """Check whether there are still sessions or tokens to remove."""
        return any(
            queryset.exists() for queryset in self._get_lockdown_artifact_querysets(stage, user)
        )

    def _emit_lockdown_event(self, request: HttpRequest, user: User, reason: str) -> None:
        """Emit the audit event for a completed lockdown."""
        # Emit the audit event after the transaction commits. If event creation
        # fails here, dispatch() would otherwise treat the whole lockdown as
        # failed even though the account changes have already been committed.
        try:
            Event.new(
                EventAction.USER_WRITE,
                action_id=LOCKDOWN_EVENT_ACTION_ID,
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

    def _lockdown_user(
        self,
        request: HttpRequest,
        stage: AccountLockdownStage,
        user: User,
        reason: str,
    ) -> None:
        """Execute lockdown actions on a single user."""
        with atomic():
            user = User.objects.get(pk=user.pk)
            self._apply_lockdown_actions(stage, user)
            self._delete_lockdown_artifacts(stage, user)

        # These additional checks/deletes are done to prevent a timing attack that creates tokens
        # with a compromised token that is simultaneously being deleted.
        while self._has_lockdown_artifacts(stage, user):
            with atomic():
                self._delete_lockdown_artifacts(stage, user)

        if stage.deactivate_user:
            try:
                self._sync_deactivated_user_to_outgoing_providers(user)
            except Exception as exc:  # noqa: BLE001
                # Local lockdown has already committed. Provider sync failures
                # must not reopen access or mark the lockdown itself as failed.
                self.logger.warning(
                    "Failed to sync account lockdown deactivation to outgoing providers",
                    user=user.username,
                    exc=exc,
                )
        self._emit_lockdown_event(request, user, reason)

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        """Execute account lockdown actions."""
        self.request = request
        stage: AccountLockdownStage = self.executor.current_stage

        pending_user = self.get_pending_user()
        if not pending_user.is_authenticated:
            self.logger.warning("No target user found for account lockdown")
            return self.executor.stage_invalid(TARGET_REQUIRED_MESSAGE)
        user = get_lockdown_target_users().filter(pk=pending_user.pk).first()
        if user is None:
            self.logger.warning("Target user is not eligible for account lockdown")
            return self.executor.stage_invalid(TARGET_REQUIRED_MESSAGE)
        if not can_lock_user(request.user, user):
            self.logger.warning(
                "Permission denied for account lockdown",
                actor=getattr(request.user, "username", None),
                target=user.username,
            )
            return self.executor.stage_invalid(PERMISSION_DENIED_MESSAGE)

        reason = self.get_reason()
        self_service = self.is_self_service(request, user)
        if self_service and stage.delete_sessions and not stage.self_service_completion_flow:
            self.logger.warning("No completion flow configured for self-service account lockdown")
            return self.executor.stage_invalid(SELF_SERVICE_COMPLETION_FLOW_REQUIRED_MESSAGE)

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
        except Exception as exc:  # noqa: BLE001
            # Convert unexpected lockdown errors to a flow-stage failure instead
            # of leaking an exception through the flow executor.
            self.logger.warning("Account lockdown failed", user=user.username, exc=exc)
            return self.executor.stage_invalid(ACCOUNT_LOCKDOWN_FAILED_MESSAGE)

        if self_service:
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
        return self.executor.stage_invalid(SELF_SERVICE_COMPLETION_FLOW_REQUIRED_MESSAGE)
