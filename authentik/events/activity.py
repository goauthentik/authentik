"""Successful user activity used by automatic expiration and refresh recording."""

from datetime import timedelta

from django.db import models
from django.db.models import OuterRef, QuerySet, Subquery

from authentik.core.models import User
from authentik.events.models import Event, EventAction

REFRESH_ACTIVITY_INTERVAL = timedelta(hours=24)
ACTIVITY_ACTIONS = (EventAction.LOGIN, EventAction.AUTHORIZE_APPLICATION, EventAction.TOKEN_REFRESH)
EXACT_ACTIVITY_ACTIONS = tuple(
    action for action in ACTIVITY_ACTIONS if action != EventAction.TOKEN_REFRESH
)


def with_activity(users: QuerySet[User]) -> QuerySet[User]:
    """Load exact activity and sampled refresh activity in the user query.

    Event identities are JSON numbers; cast the outer user ID so PostgreSQL can
    compare it to the indexed JSON expression without casting the event column.
    """
    events = Event.objects.filter(
        user__pk=models.Func(OuterRef("pk"), function="to_jsonb", output_field=models.JSONField())
    )
    return users.annotate(
        expiration_event_at=Subquery(
            events.filter(action__in=EXACT_ACTIVITY_ACTIONS)
            .order_by("-created")
            .values("created")[:1]
        ),
        expiration_refresh_at=Subquery(
            events.filter(action=EventAction.TOKEN_REFRESH)
            .order_by("-created")
            .values("created")[:1]
        ),
    )


def load_activity(user: User) -> None:
    """Refresh activity once, then share it between competing rules."""
    loaded = with_activity(User.objects.filter(pk=user.pk)).get()
    for field in ("expiration_event_at", "expiration_refresh_at"):
        setattr(user, field, getattr(loaded, field))
