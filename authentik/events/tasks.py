"""Event notification tasks"""
from guardian.shortcuts import get_anonymous_user
from structlog import get_logger

from authentik.events.models import (
    Event,
    Notification,
    NotificationRule,
    NotificationTransport,
    NotificationTransportError,
)
from authentik.events.monitored_tasks import MonitoredTask, TaskResult, TaskResultStatus
from authentik.policies.engine import PolicyEngine, PolicyEngineMode
from authentik.policies.models import PolicyBinding
from authentik.root.celery import CELERY_APP

LOGGER = get_logger()


@CELERY_APP.task()
def event_notification_handler(event_uuid: str):
    """Start task for each trigger definition"""
    for trigger in NotificationRule.objects.all():
        event_trigger_handler.apply_async(
            args=[event_uuid, trigger.name], queue="authentik_events"
        )


@CELERY_APP.task()
def event_trigger_handler(event_uuid: str, trigger_name: str):
    """Check if policies attached to NotificationRule match event"""
    event: Event = Event.objects.get(event_uuid=event_uuid)
    trigger: NotificationRule = NotificationRule.objects.get(name=trigger_name)

    if "policy_uuid" in event.context:
        policy_uuid = event.context["policy_uuid"]
        if PolicyBinding.objects.filter(
            target__in=NotificationRule.objects.all().values_list(
                "pbm_uuid", flat=True
            ),
            policy=policy_uuid,
        ).exists():
            # If policy that caused this event to be created is attached
            # to *any* NotificationRule, we return early.
            # This is the most effective way to prevent infinite loops.
            LOGGER.debug(
                "e(trigger): attempting to prevent infinite loop", trigger=trigger
            )
            return

    if not trigger.group:
        LOGGER.debug("e(trigger): trigger has no group", trigger=trigger)
        return

    LOGGER.debug("e(trigger): checking if trigger applies", trigger=trigger)
    policy_engine = PolicyEngine(trigger, get_anonymous_user())
    policy_engine.mode = PolicyEngineMode.MODE_OR
    policy_engine.empty_result = False
    policy_engine.use_cache = False
    policy_engine.request.context["event"] = event
    policy_engine.build()
    result = policy_engine.result
    if not result.passing:
        return

    LOGGER.debug("e(trigger): event trigger matched", trigger=trigger)
    # Create the notification objects
    for user in trigger.group.users.all():
        notification = Notification.objects.create(
            severity=trigger.severity, body=event.summary, event=event, user=user
        )

        for transport in trigger.transports.all():
            notification_transport.apply_async(
                args=[notification.pk, transport.pk], queue="authentik_events"
            )


@CELERY_APP.task(
    bind=True,
    autoretry_for=(NotificationTransportError,),
    retry_backoff=True,
    base=MonitoredTask,
)
def notification_transport(
    self: MonitoredTask, notification_pk: int, transport_pk: int
):
    """Send notification over specified transport"""
    self.save_on_success = False
    try:
        notification: Notification = Notification.objects.get(pk=notification_pk)
        transport: NotificationTransport = NotificationTransport.objects.get(
            pk=transport_pk
        )
        transport.send(notification)
        self.set_status(TaskResult(TaskResultStatus.SUCCESSFUL))
    except NotificationTransportError as exc:
        self.set_status(TaskResult(TaskResultStatus.ERROR).with_error(exc))
        raise exc
