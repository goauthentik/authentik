"""PAM access-request notification tasks"""

from uuid import UUID

from django.utils.translation import gettext_lazy as _
from dramatiq.actor import actor

from authentik.core.models import User
from authentik.events.models import Event, Notification, NotificationSeverity, NotificationTransport


@actor(description=_("Send access-request review notification."))
def requests_send_request_notification(transport_pk: UUID, event_pk: UUID, user_pk: int):
    """Send a single review notification over the given transport, to the given user"""
    event = Event.objects.filter(pk=event_pk).first()
    if not event:
        return
    user = User.objects.filter(pk=user_pk).first()
    if not user:
        return
    transport = NotificationTransport.objects.filter(pk=transport_pk).first()
    if not transport:
        return
    notification = Notification(
        severity=NotificationSeverity.NOTICE,
        body=event.summary,
        event=event,
        user=user,
        hyperlink=event.hyperlink,
        hyperlink_label=event.hyperlink_label,
    )
    transport.send(notification)
