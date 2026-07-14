"""Shared user offboarding logic.

This is the single place that actually deactivates/deletes a user and revokes
their access. The single-user offboarding feature uses it via a scheduled
sweeper task, and the upcoming policy-driven action lifecycle will reuse it too.
"""

from django.http import HttpRequest
from django.utils.translation import gettext as _
from structlog.stdlib import get_logger

from authentik.core.models import User
from authentik.enterprise.core.revocation import revoke_user_access
from authentik.enterprise.lifecycle.models import OffboardingAction
from authentik.events.models import Event, EventAction

LOGGER = get_logger()


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

    The audit event is attributed to the initiator (request user, or the
    scheduling admin via `initiator`) — never to the offboarded user.
    """
    username = user.username
    user_pk = user.pk

    revoke_user_access(user, sessions=revoke_sessions, tokens=revoke_tokens)

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
