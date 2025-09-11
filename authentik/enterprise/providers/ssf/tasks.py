from typing import Any
from uuid import UUID

from django.http import HttpRequest
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django_dramatiq_postgres.middleware import CurrentTask
from dramatiq.actor import actor
from requests.exceptions import RequestException
from structlog.stdlib import get_logger

from authentik.core.models import User
from authentik.enterprise.providers.ssf.models import (
    DeliveryMethods,
    EventTypes,
    SSFEventStatus,
    Stream,
    StreamEvent,
)
from authentik.lib.utils.http import get_http_session
from authentik.lib.utils.time import timedelta_from_string
from authentik.policies.engine import PolicyEngine
from authentik.tasks.models import Task

session = get_http_session()
LOGGER = get_logger()


def send_ssf_events(
    event_type: EventTypes,
    data: dict,
    stream_filter: dict | None = None,
    request: HttpRequest | None = None,
    **extra_data,
):
    """Wrapper to send an SSF event to multiple streams"""
    events_data = {}
    if not stream_filter:
        stream_filter = {}
    stream_filter["events_requested__contains"] = [event_type]
    if request and hasattr(request, "request_id"):
        extra_data.setdefault("txn", request.request_id)
    for stream in Stream.objects.filter(**stream_filter):
        event_data = stream.prepare_event_payload(event_type, data, **extra_data)
        events_data[stream.uuid] = event_data
    ssf_events_dispatch.send(events_data)


@actor(description=_("Dispatch SSF events."))
def ssf_events_dispatch(events_data: dict[str, dict[str, Any]]):
    for stream_uuid, event_data in events_data.items():
        stream = Stream.objects.filter(pk=stream_uuid).first()
        if not stream:
            continue
        send_ssf_event.send_with_options(args=(stream_uuid, event_data), rel_obj=stream.provider)


def _check_app_access(stream: Stream, event_data: dict) -> bool:
    """Check if event is related to user and if so, check
    if the user has access to the application"""
    # `event_data` is a dict version of a StreamEvent
    sub_id = event_data.get("payload", {}).get("sub_id", {})
    email = sub_id.get("user", {}).get("email", None)
    if not email:
        return True
    user = User.objects.filter(email=email).first()
    if not user:
        return True
    engine = PolicyEngine(stream.provider.backchannel_application, user)
    engine.use_cache = False
    engine.build()
    return engine.passing


@actor(description=_("Send an SSF event."))
def send_ssf_event(stream_uuid: UUID, event_data: dict[str, Any]):
    self: Task = CurrentTask.get_task()

    stream = Stream.objects.filter(pk=stream_uuid).first()
    if not stream:
        return
    if not _check_app_access(stream, event_data):
        return
    event = StreamEvent.objects.create(**event_data)
    self.set_uid(event.pk)
    if event.status == SSFEventStatus.SENT:
        return
    if stream.delivery_method != DeliveryMethods.RISC_PUSH:
        return

    try:
        response = session.post(
            event.stream.endpoint_url,
            data=event.stream.encode(event.payload),
            headers={"Content-Type": "application/secevent+jwt", "Accept": "application/json"},
        )
        response.raise_for_status()
        event.status = SSFEventStatus.SENT
        event.save()
        return
    except RequestException as exc:
        LOGGER.warning("Failed to send SSF event", exc=exc)
        attrs = {}
        if exc.response:
            attrs["response"] = {
                "content": exc.response.text,
                "status": exc.response.status_code,
            }
        self.warning(exc)
        self.warning("Failed to send request", **attrs)
        # Re-up the expiry of the stream event
        event.expires = now() + timedelta_from_string(event.stream.provider.event_retention)
        event.status = SSFEventStatus.PENDING_FAILED
        event.save()
