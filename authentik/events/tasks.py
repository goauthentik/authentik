"""Event notification tasks"""

from uuid import UUID

from django.db.models import Prefetch, Q, QuerySet
from django.utils.translation import gettext_lazy as _
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
from authentik.lib.utils.db import chunked_queryset
from authentik.policies.engine import PolicyEngine
from authentik.policies.models import PolicyBinding, PolicyEngineMode
from authentik.tasks.middleware import CurrentTask

LOGGER = get_logger()


@actor(description=_("Dispatch new event notifications."))
def event_trigger_dispatch(event_uuid: UUID):
    """Check all NotificationRules against an event in one pass"""
    _evaluate_rules(event_uuid, NotificationRule.objects.all())


@actor(
    description=_(
        "Check if policies attached to NotificationRule match event "
        "and dispatch notification tasks."
    )
)
def event_trigger_handler(event_uuid: UUID, trigger_name: str):
    """Check if policies attached to NotificationRule match event"""
    # only kept for messages enqueued before upgrading, remove in a later release
    _evaluate_rules(event_uuid, NotificationRule.objects.filter(name=trigger_name))


def _evaluate_rules(event_uuid: UUID, rules: QuerySet[NotificationRule]):
    self = CurrentTask.get_task()

    event: Event = Event.objects.filter(event_uuid=event_uuid).first()
    if not event:
        self.warning("event doesn't exist yet or anymore", event_uuid=event_uuid)
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
            LOGGER.debug("e(trigger): attempting to prevent infinite loop", event=event)
            return

    rules = rules.prefetch_related(
        Prefetch(
            "bindings",
            queryset=PolicyBinding.objects.filter(enabled=True)
            .select_related("user", "group")
            .order_by("order"),
            to_attr="enabled_bindings",
        ),
        # Resolves policy subclasses for all bindings in one query
        "enabled_bindings__policy",
        "transports",
    )
    # Rules without bindings never match (empty_result is False below)
    rules = [rule for rule in rules if rule.enabled_bindings]
    if not rules:
        return

    user = User.objects.filter(pk=event.user.get("pk")).first() or get_anonymous_user()
    count = 0
    for trigger in rules:
        LOGGER.debug("e(trigger): checking if trigger applies", trigger=trigger)
        policy_engine = PolicyEngine(trigger, user, bindings=trigger.enabled_bindings)
        policy_engine.mode = PolicyEngineMode.MODE_ANY
        policy_engine.empty_result = False
        policy_engine.use_cache = False
        policy_engine.request.obj = event
        policy_engine.request.context["event"] = event
        policy_engine.build()
        if not policy_engine.result.passing:
            continue

        LOGGER.debug("e(trigger): event trigger matched", trigger=trigger)
        # Create the notification objects
        for transport in trigger.transports.all():
            for destination in trigger.destination_users(event):
                notification_transport.send_with_options(
                    args=(
                        transport.pk,
                        event.pk,
                        destination.pk,
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
        severity=trigger.severity,
        body=event.summary,
        event=event,
        user=user,
        hyperlink=event.hyperlink,
        hyperlink_label=event.hyperlink_label,
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
    for event in chunked_queryset(events):
        event.delete()


@actor(description=_("Cleanup seen notifications and notifications whose event expired."))
def notification_cleanup():
    """Cleanup seen notifications and notifications whose event expired."""
    self = CurrentTask.get_task()
    notifications = Notification.objects.filter(Q(event=None) | Q(seen=True))
    amount = notifications.count()
    notifications.delete()
    LOGGER.debug("Expired notifications", amount=amount)
    self.info(f"Expired {amount} Notifications")
