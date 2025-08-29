"""Event notification tasks"""

from uuid import UUID

from django.db.models.query_utils import Q
from django.utils.translation import gettext_lazy as _
from django_dramatiq_postgres.middleware import CurrentTask
from dramatiq.actor import actor
from guardian.shortcuts import get_anonymous_user
from structlog.stdlib import get_logger

from authentik.core.models import User
from authentik.events.models import (
    Event,
    Notification,
    NotificationRule,
    NotificationTransport,
)
from authentik.policies.engine import PolicyEngine
from authentik.policies.models import PolicyBinding, PolicyEngineMode
from authentik.tasks.models import Task

LOGGER = get_logger()


@actor(description=_("Dispatch new event notifications."))
def event_trigger_dispatch(event_uuid: UUID):
    for trigger in NotificationRule.objects.all():
        event_trigger_handler.send_with_options(args=(event_uuid, trigger.name), rel_obj=trigger)


@actor(
    description=_(
        "Check if policies attached to NotificationRule match event "
        "and dispatch notification tasks."
    )
)
def event_trigger_handler(event_uuid: UUID, trigger_name: str):
    """Check if policies attached to NotificationRule match event"""
    self: Task = CurrentTask.get_task()

    event: Event = Event.objects.filter(event_uuid=event_uuid).first()
    if not event:
        self.warning("event doesn't exist yet or anymore", event_uuid=event_uuid)
        return

    trigger: NotificationRule | None = NotificationRule.objects.filter(name=trigger_name).first()
    if not trigger:
        return

    if "policy_uuid" in event.context:
        policy_uuid = event.context["policy_uuid"]
        if PolicyBinding.objects.filter(
            target__in=NotificationRule.objects.all().values_list("pbm_uuid", flat=True),
            policy=policy_uuid,
        ).exists():
            # If policy that caused this event to be created is attached
            # to *any* NotificationRule, we return early.
            # This is the most effective way to prevent infinite loops.
            LOGGER.debug("e(trigger): attempting to prevent infinite loop", trigger=trigger)
            return

    LOGGER.debug("e(trigger): checking if trigger applies", trigger=trigger)
    try:
        user = User.objects.filter(pk=event.user.get("pk")).first() or get_anonymous_user()
    except User.DoesNotExist:
        LOGGER.warning("e(trigger): failed to get user", trigger=trigger)
        return
    policy_engine = PolicyEngine(trigger, user)
    policy_engine.mode = PolicyEngineMode.MODE_ANY
    policy_engine.empty_result = False
    policy_engine.use_cache = False
    policy_engine.request.obj = event
    policy_engine.request.context["event"] = event
    policy_engine.build()
    result = policy_engine.result
    if not result.passing:
        return

    LOGGER.debug("e(trigger): event trigger matched", trigger=trigger)
    # Create the notification objects
    count = 0
    for transport in trigger.transports.all():
        for user in trigger.destination_users(event):
            notification_transport.send_with_options(
                args=(
                    transport.pk,
                    event.pk,
                    user.pk,
                    trigger.pk,
                ),
                rel_obj=transport,
            )
            count += 1
            if transport.send_once:
                break
    self.info(f"Created {count} notification tasks")


@actor(description=_("Send notification."))
def notification_transport(transport_pk: int, event_pk: str, user_pk: int, trigger_pk: str):
    """Send notification over specified transport"""
    event = Event.objects.filter(pk=event_pk).first()
    if not event:
        return
    user = User.objects.filter(pk=user_pk).first()
    if not user:
        return
    trigger = NotificationRule.objects.filter(pk=trigger_pk).first()
    if not trigger:
        return
    notification = Notification(
        severity=trigger.severity, body=event.summary, event=event, user=user
    )
    transport: NotificationTransport = NotificationTransport.objects.filter(pk=transport_pk).first()
    if not transport:
        return
    transport.send(notification)


@actor(description=_("Cleanup events for GDPR compliance."))
def gdpr_cleanup(user_pk: int):
    """cleanup events from gdpr_compliance"""
    events = Event.objects.filter(user__pk=user_pk)
    LOGGER.debug("GDPR cleanup, removing events from user", events=events.count())
    events.delete()


@actor(description=_("Cleanup seen notifications and notifications whose event expired."))
def notification_cleanup():
    """Cleanup seen notifications and notifications whose event expired."""
    self: Task = CurrentTask.get_task()
    notifications = Notification.objects.filter(Q(event=None) | Q(seen=True))
    amount = notifications.count()
    notifications.delete()
    LOGGER.debug("Expired notifications", amount=amount)
    self.info(f"Expired {amount} Notifications")
