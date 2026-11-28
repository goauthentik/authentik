"""Pre-filter deciding which events can trigger a notification rule"""

from time import monotonic

from django.db import connection
from django.db.models import Count, Q

from authentik.events.models import NotificationRule
from authentik.policies.models import PolicyBinding

CACHE_TIMEOUT = 30

# Bindings that can pass for any event action, or that log an event when evaluated
ANY_ACTION = (
    # Also true for user/group bindings and other policy types
    Q(policy__eventmatcherpolicy__action__isnull=True)
    | Q(policy__eventmatcherpolicy__action="")
    | Q(policy__execution_logging=True)
    | Q(negate=True)
    | Q(dry_run=True)
    | Q(failure_result=True)
)

# (schema name, action or None for any action) -> time until which events are dispatched without
# a query. Only "could match" is remembered, an outdated "can't match" would lose a notification.
_dispatch_until: dict[tuple[str, str | None], float] = {}


def could_match_notification_rule(action: str) -> bool:
    """Check if any NotificationRule could match an event with `action`"""
    now = monotonic()
    schema = connection.schema_name
    if max(_dispatch_until.get((schema, None), 0), _dispatch_until.get((schema, action), 0)) > now:
        return True
    # Rules are evaluated in MODE_ANY, so a rule can only match if one of its enabled bindings can
    matches = PolicyBinding.objects.filter(
        enabled=True, target__in=NotificationRule.objects.values("pk")
    ).aggregate(
        any_action=Count("pk", filter=ANY_ACTION),
        action=Count("pk", filter=Q(policy__eventmatcherpolicy__action=action)),
    )
    if matches["any_action"]:
        _dispatch_until[(schema, None)] = now + CACHE_TIMEOUT
        return True
    if matches["action"]:
        _dispatch_until[(schema, action)] = now + CACHE_TIMEOUT
        return True
    return False


def clear_cache() -> None:
    """Forget which actions could match"""
    _dispatch_until.clear()
