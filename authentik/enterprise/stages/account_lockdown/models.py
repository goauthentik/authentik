"""Account lockdown stage models"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.flows.models import Stage


class AccountLockdownStage(Stage):
    """Lock down a target user account."""

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
        help_text=_(
            "Revoke all tokens for the user (API, app password, recovery, verification, OAuth)"
        ),
    )
    self_service_completion_flow = models.ForeignKey(
        "authentik_flows.Flow",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="account_lockdown_stages",
        help_text=_(
            "Flow to redirect users to after self-service lockdown. "
            "This flow should not require authentication since the user's session is deleted."
        ),
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
