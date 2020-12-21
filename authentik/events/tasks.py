"""Event Alerting tasks"""
from guardian.shortcuts import get_anonymous_user
from structlog import get_logger

from authentik.events.models import Event, EventAlertTrigger
from authentik.policies.engine import PolicyEngine
from authentik.root.celery import CELERY_APP

LOGGER = get_logger()


@CELERY_APP.task()
def event_alert_handler(event_uuid: str):
    """Start task for each trigger definition"""
    for trigger in EventAlertTrigger.objects.all():
        event_trigger_handler.apply_async(
            args=[event_uuid, trigger.name], queue="authentik_events"
        )


@CELERY_APP.task()
def event_trigger_handler(event_uuid: str, trigger_name: str):
    """Check if policies attached to EventAlertTrigger match event"""
    event: Event = Event.objects.get(event_uuid=event_uuid)
    trigger: EventAlertTrigger = EventAlertTrigger.objects.get(name=trigger_name)

    if "policy_uuid" in event.context:
        policy_uuid = event.context["policy_uuid"]
        if trigger.policies.filter(policy_uuid=policy_uuid).exists():
            # Event has been created by a policy that is attached
            # to this trigger. To prevent infinite loops, we stop here
            LOGGER.debug("e(trigger): attempting to prevent infinite loop")
            return

    if not trigger.action:
        LOGGER.debug("e(trigger): event trigger has no action")
        return

    policy_engine = PolicyEngine(trigger, get_anonymous_user())
    policy_engine.request.context["event"] = event
    policy_engine.build()
    result = policy_engine.result
    if result.passing:
        LOGGER.debug("e(trigger): event trigger matched")
        trigger.action.execute(event)
