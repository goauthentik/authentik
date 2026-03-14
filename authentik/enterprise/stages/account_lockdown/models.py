"""Account lockdown stage models"""

from django.db import models
from django.utils.html import escape
from django.utils.translation import gettext as gettext
from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext_noop
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.flows.models import Stage

# Context keys for account lockdown
PLAN_CONTEXT_LOCKDOWN_TARGETS = "lockdown_target_users"
PLAN_CONTEXT_LOCKDOWN_REASON = "lockdown_reason"
PLAN_CONTEXT_LOCKDOWN_SELF_SERVICE = "lockdown_self_service"
PLAN_CONTEXT_LOCKDOWN_RESULT = "lockdown_result"  # {user, success, error}

DEFAULT_SELF_SERVICE_MESSAGE_TITLE = gettext_noop("Your account has been locked")
DEFAULT_SELF_SERVICE_MESSAGE = gettext_noop(
    "<p>You have been logged out of all sessions and your password has been "
    "invalidated.</p>"
    "<p>To regain access to your account, please contact your IT administrator "
    "or security team.</p>"
)
SELF_SERVICE_FAILURE_MESSAGE_TITLE = gettext_noop("Account lockdown failed")
SELF_SERVICE_FAILURE_MESSAGE = gettext_noop(
    "<p>We could not lock your account. Please contact your administrator or "
    "security team for assistance.</p>"
)
TARGET_REQUIRED_MESSAGE = gettext_noop("No target user specified for account lockdown")
ACCOUNT_LOCKDOWN_FAILED_MESSAGE = gettext_noop("Account lockdown failed for this account.")
LOCKDOWN_TARGET_FALLBACK = gettext_noop(
    "the account selected when this one-time lockdown link was created"
)
LOCKDOWN_TARGET_NO_EMAIL = gettext_noop("No email")
LOCKDOWN_WARNING_SELF_SERVICE = gettext_noop(
    "<p><strong>You are about to lock down your own account.</strong></p>"
    "<p>This is an emergency action for cutting off access to your account right away.</p>"
    "<p><strong>This will immediately:</strong></p>"
    "<ul>"
    "<li><strong>Invalidate your password</strong> - Your password will be set to a random value "
    "and cannot be recovered</li>"
    "<li><strong>Deactivate your account</strong> - Your account will be disabled</li>"
    "<li><strong>Terminate all your sessions</strong> - You will be logged out everywhere</li>"
    "<li><strong>Revoke all your tokens</strong> - All your API, app password, recovery, and "
    "verification tokens will be revoked</li>"
    "</ul>"
    "<p><strong>This action cannot be easily undone.</strong></p>"
)
LOCKDOWN_WARNING_ADMIN = gettext_noop(
    "<p><strong>You are about to lock down the following account:</strong></p>"
    "{user_list}"
    "<p>This is an emergency action for cutting off access to that account right away. "
    "It does not lock the administrator who opened this page.</p>"
    "<p><strong>This will immediately:</strong></p>"
    "<ul>"
    "<li>Invalidate passwords - Passwords will be set to random values</li>"
    "<li>Deactivate accounts - Accounts will be disabled</li>"
    "<li>Terminate all sessions - All active sessions will be ended</li>"
    "<li>Revoke all tokens - All API, app password, recovery, and verification tokens "
    "will be revoked</li>"
    "</ul>"
    "<p><strong>This action cannot be easily undone.</strong></p>"
)
LOCKDOWN_INFO_SELF_SERVICE = gettext_noop(
    "Use this if you no longer trust your current password or sessions. "
    "After lockdown, you will need help from your administrator or security team to regain access."
)
LOCKDOWN_INFO_ADMIN = gettext_noop(
    "Use this for incident response on the listed account, for example after a compromise report "
    "or suspicious activity. The reason you enter below will be recorded in the audit log."
)
LOCKDOWN_INFO_LINK = gettext_noop("Learn more about account lockdown")
LOCKDOWN_REASON_PLACEHOLDER_SELF_SERVICE = gettext_noop(
    "Describe why you are locking your account..."
)
LOCKDOWN_REASON_PLACEHOLDER_ADMIN = gettext_noop(
    "Describe why this account is being locked down..."
)
LOCKDOWN_COMPLETE_DEFAULT = gettext_noop("The account has been locked down.")
LOCKDOWN_COMPLETE_SUCCESS = gettext_noop("{username} has been locked down.")
LOCKDOWN_COMPLETE_FAILURE = gettext_noop("Failed to lock down {username}: {error}")


# Keep shared lockdown copy in Python so both stage responses and blueprint
# expressions share one source of truth for translated text and rendered HTML.
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


def get_lockdown_target_html(target) -> str:
    """Render the account summary shown in admin lockdown prompts."""
    if target:
        email = escape(
            target.email or target.name or translate_lockdown_text(LOCKDOWN_TARGET_NO_EMAIL)
        )
        return f"<p><code>{escape(target.username)}</code> ({email})</p>"
    return f"<p>{escape(translate_lockdown_text(LOCKDOWN_TARGET_FALLBACK))}</p>"


def get_lockdown_warning_html(*, self_service: bool, target=None) -> str:
    """Render the warning body shown before executing lockdown."""
    if self_service:
        return translate_lockdown_text(LOCKDOWN_WARNING_SELF_SERVICE)
    return translate_lockdown_text(LOCKDOWN_WARNING_ADMIN).format(
        user_list=get_lockdown_target_html(target)
    )


def get_lockdown_info_html(*, self_service: bool) -> str:
    """Render the informational helper text for lockdown prompts."""
    info = LOCKDOWN_INFO_SELF_SERVICE if self_service else LOCKDOWN_INFO_ADMIN
    learn_more = translate_lockdown_text(LOCKDOWN_INFO_LINK)
    return (
        f"<p>{translate_lockdown_text(info)}</p>"
        '<p><a href="https://docs.goauthentik.io/docs/security/account-lockdown?utm_source=authentik" '
        f'target="_blank" rel="noopener noreferrer">{learn_more}</a></p>'
    )


def get_lockdown_reason_placeholder(*, self_service: bool) -> str:
    """Render the localized lockdown-reason placeholder."""
    key = (
        LOCKDOWN_REASON_PLACEHOLDER_SELF_SERVICE
        if self_service
        else LOCKDOWN_REASON_PLACEHOLDER_ADMIN
    )
    return translate_lockdown_text(key)


def get_lockdown_completion_html(result: dict | None) -> str:
    """Render the admin completion message body."""
    if not result:
        return f"<p>{translate_lockdown_text(LOCKDOWN_COMPLETE_DEFAULT)}</p>"

    user = result.get("user")
    username = f"<code>{escape(user.username if user else 'Unknown')}</code>"
    if result.get("success"):
        return (
            f"<p>{translate_lockdown_text(LOCKDOWN_COMPLETE_SUCCESS).format(username=username)}</p>"
        )

    error = escape(result.get("error", "Unknown error"))
    return f"<p>{translate_lockdown_text(LOCKDOWN_COMPLETE_FAILURE).format(username=username, error=error)}</p>"


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
            "Revoke all tokens for the user " "(API, app password, recovery, verification, OAuth2)"
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
