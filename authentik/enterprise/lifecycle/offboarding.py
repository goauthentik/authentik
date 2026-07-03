"""Shared user offboarding logic.

This is the single place that actually deactivates/deletes a user and revokes
their access. The single-user offboarding feature uses it via a scheduled
sweeper task, and the upcoming policy-driven action lifecycle will reuse it too.
"""

from django.http import HttpRequest
from django.utils.translation import gettext as _
from structlog.stdlib import get_logger

from authentik.core.models import AuthenticatedSession, Token, User
from authentik.enterprise.lifecycle.models import OffboardingAction
from authentik.events.models import Event, EventAction

LOGGER = get_logger()


def revoke_sessions_for_user(user: User) -> int:
    """Delete all of a user's authenticated sessions."""
    deleted, _ = AuthenticatedSession.objects.filter(user=user).delete()
    return deleted


def revoke_tokens_for_user(user: User) -> int:
    """Delete all of a user's tokens (API access, app passwords, recovery, ...)."""
    deleted, _ = Token.objects.filter(user=user).delete()
    return deleted


def offboard_user(
    user: User,
    action: str,
    *,
    revoke_sessions: bool = True,
    revoke_tokens: bool = True,
    request: HttpRequest | None = None,
    initiator: User | None = None,
):
    """Offboard `user` by applying `action`, optionally revoking sessions/tokens.

    The event is built and saved before any destructive action so that a
    `DELETE` (which cascades this user's related rows away) is still audited.

    The audit event is attributed to whoever initiated the offboarding: the
    request user when run interactively, or `initiator` (the admin who scheduled
    it) when run from the background sweeper. It is never attributed to the
    offboarded user themselves.
    """
    username = user.username
    user_pk = user.pk

    if revoke_sessions:
        revoke_sessions_for_user(user)
    if revoke_tokens:
        revoke_tokens_for_user(user)

    event = Event.new(
        EventAction.USER_OFFBOARDED,
        message=_("User %(username)s was offboarded (%(action)s)")
        % {"username": username, "action": action},
        offboarding_action=action,
        revoke_sessions=revoke_sessions,
        revoke_tokens=revoke_tokens,
        user_pk=user_pk,
    )
    if request is not None:
        event.from_http(request, user=initiator)
    else:
        if initiator is not None:
            event.set_user(initiator)
        event.save()

    if action == OffboardingAction.DEACTIVATE:
        user.is_active = False
        user.save(update_fields=["is_active"])
    elif action == OffboardingAction.DELETE:
        user.delete()
    else:
        LOGGER.warning("Unknown offboarding action", action=action, user=username)
