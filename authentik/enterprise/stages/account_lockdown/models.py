"""Account lockdown stage models"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.flows.models import Stage

# Context keys for account lockdown
PLAN_CONTEXT_LOCKDOWN_TARGET = "lockdown_target_user"
PLAN_CONTEXT_LOCKDOWN_REASON = "lockdown_reason"
PLAN_CONTEXT_LOCKDOWN_SELF_SERVICE = "lockdown_self_service"


class AccountLockdownStage(Stage):
    """Execute account lockdown actions within a flow.

    This stage performs one or more of the following actions on a target user:
    - Deactivate the user account
    - Set an unusable password
    - Delete all active sessions
    - Revoke all API and app password tokens

    The target user is read from PLAN_CONTEXT_LOCKDOWN_TARGET or PLAN_CONTEXT_PENDING_USER.
    The reason is read from prompt_data['reason'] or PLAN_CONTEXT_LOCKDOWN_REASON."""

    deactivate_user = models.BooleanField(
        default=True,
        help_text=_("Deactivate the user account (set is_active to False)"),
    )
    set_unusable_password = models.BooleanField(
        default=True,
        help_text=_("Set an unusable password for the user"),
    )
    delete_sessions = models.BooleanField(
        default=True,
        help_text=_("Delete all active sessions for the user"),
    )
    revoke_tokens = models.BooleanField(
        default=True,
        help_text=_("Revoke all API and app password tokens for the user"),
    )

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.enterprise.stages.account_lockdown.api import AccountLockdownStageSerializer

        return AccountLockdownStageSerializer

    @property
    def view(self) -> type[View]:
        from authentik.enterprise.stages.account_lockdown.stage import AccountLockdownStageView

        return AccountLockdownStageView

    @property
    def component(self) -> str:
        return "ak-stage-account-lockdown-form"

    class Meta:
        verbose_name = _("Account Lockdown Stage")
        verbose_name_plural = _("Account Lockdown Stages")
