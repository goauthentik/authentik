"""Account lockdown stage models"""

from django.db import models
from django.utils.html import escape
from django.utils.translation import gettext as gettext
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.flows.models import Stage

# Context keys for account lockdown
PLAN_CONTEXT_LOCKDOWN_TARGETS = "lockdown_target_users"
PLAN_CONTEXT_LOCKDOWN_REASON = "lockdown_reason"
PLAN_CONTEXT_LOCKDOWN_SELF_SERVICE = "lockdown_self_service"
PLAN_CONTEXT_LOCKDOWN_RESULT = "lockdown_result"  # {user, success, error}

DEFAULT_SELF_SERVICE_MESSAGE_TITLE = "Your account has been locked"
DEFAULT_SELF_SERVICE_MESSAGE = (
    "<p>You have been logged out of all sessions and your password has been "
    "invalidated.</p>"
    "<p>To regain access to your account, please contact your IT administrator "
    "or security team.</p>"
)
SELF_SERVICE_FAILURE_MESSAGE_TITLE = "Account lockdown failed"
SELF_SERVICE_FAILURE_MESSAGE = (
    "<p>We could not lock your account. Please contact your administrator or "
    "security team for assistance.</p>"
)
TARGET_REQUIRED_MESSAGE = "No target user specified for account lockdown"
ACCOUNT_LOCKDOWN_FAILED_MESSAGE = "Account lockdown failed for this account."


# Keep shared lockdown copy in Python so both stage responses and blueprint
# expressions use one source of truth and go through Django's normal gettext path.
def translate_lockdown_text(message: str) -> str:
    return gettext(message)


def render_lockdown_message_html(title: str, body: str) -> str:
    """Render the shared lockdown message markup."""
    return f"<h1>{escape(title)}</h1>{body}"


def get_default_self_service_message_html() -> str:
    """Render the default self-service completion markup."""
    return render_lockdown_message_html(
        translate_lockdown_text(DEFAULT_SELF_SERVICE_MESSAGE_TITLE),
        translate_lockdown_text(DEFAULT_SELF_SERVICE_MESSAGE),
    )


class AccountLockdownStage(Stage):
    """Execute account lockdown actions within a flow.

    This stage performs the following actions on a target user:
    - Deactivate the user account
    - Set an unusable password
    - Delete all active sessions
    - Revoke all API and app password tokens

    The target user is read from a single-element PLAN_CONTEXT_LOCKDOWN_TARGETS list,
    PLAN_CONTEXT_PENDING_USER, or the authenticated request user for direct self-service
    execution.
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
        help_text=_(
            "Revoke all tokens for the user "
            "(API, app password, recovery, verification, OAuth2)"
        ),
    )
    self_service_message_title = models.TextField(
        default=DEFAULT_SELF_SERVICE_MESSAGE_TITLE,
        help_text=_("Title shown to users after self-service lockdown"),
    )
    self_service_message = models.TextField(
        default=DEFAULT_SELF_SERVICE_MESSAGE,
        help_text=_(
            "HTML message shown to users after self-service lockdown. Supports HTML formatting."
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
