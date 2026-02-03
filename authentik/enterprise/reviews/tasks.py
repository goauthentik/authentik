from django.utils.translation import gettext_lazy as _
from dramatiq import actor

from authentik.core.models import User
from authentik.enterprise.reviews.models import LifecycleRule
from authentik.events.models import Event, Notification, NotificationTransport


@actor(description=_("Apply object lifecycle rules."))
def apply_lifecycle_rules():
    for rule in LifecycleRule.objects.all():
        apply_lifecycle_rule.send_with_options(
            args=(rule.id,),
            rel_obj=rule,
        )

@actor(description=_("Apply lifecycle rule."))
def apply_lifecycle_rule(rule_id: str):
    rule = LifecycleRule.objects.filter(pk=rule_id).first()
    if rule:
        rule.apply()

@actor(description=_("Send notification."))
def send_notification(transport_pk: int, event_pk: str, user_pk: int, severity: str):
    event = Event.objects.filter(pk=event_pk).first()
    if not event:
        return
    user = User.objects.filter(pk=user_pk).first()
    if not user:
        return

    notification = Notification(
        severity=severity,
        body=event.summary,
        event=event,
        user=user,
        hyperlink=event.hyperlink,
        hyperlink_label=event.hyperlink_label,
    )
    transport = NotificationTransport.objects.filter(pk=transport_pk).first()
    if not transport:
        return
    transport.send(notification)
