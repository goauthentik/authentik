from django.http import HttpRequest
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from dramatiq.actor import actor
from dramatiq.composition import group
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
from authentik.events.logs import LogEvent
from authentik.lib.utils.http import get_http_session
from authentik.lib.utils.time import timedelta_from_string
from authentik.policies.engine import PolicyEngine
from authentik.tasks.middleware import CurrentTask
from authentik.tasks.models import Task, TaskStatus

session = get_http_session()
LOGGER = get_logger()


def send_ssf_event(
    event_type: EventTypes,
    data: dict,
    stream_filter: dict | None = None,
    request: HttpRequest | None = None,
    **extra_data,
):
    """Wrapper to send an SSF event to multiple streams"""
    payload = []
    if not stream_filter:
        stream_filter = {}
    stream_filter["events_requested__contains"] = [event_type]
    if request and hasattr(request, "request_id"):
        extra_data.setdefault("txn", request.request_id)
    for stream in Stream.objects.filter(**stream_filter):
        event_data = stream.prepare_event_payload(event_type, data, **extra_data)
        payload.append((str(stream.uuid), event_data))
    return _send_ssf_event.send(payload)


def _check_app_access(stream_uuid: str, event_data: dict) -> bool:
    """Check if event is related to user and if so, check
    if the user has access to the application"""
    stream = Stream.objects.filter(pk=stream_uuid).first()
    if not stream:
        return False
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


@actor
def _send_ssf_event(event_data: list[tuple[str, dict]]):
    tasks = []
    for stream, data in event_data:
        if not _check_app_access(stream, data):
            continue
        event = StreamEvent.objects.create(**data)
        tasks.extend(send_single_ssf_event(stream, str(event.uuid)))
    main_task = group(tasks)
    main_task.run()


def send_single_ssf_event(stream_id: str, evt_id: str):
    stream = Stream.objects.filter(pk=stream_id).first()
    if not stream:
        return []
    event = StreamEvent.objects.filter(pk=evt_id).first()
    if not event:
        return []
    if event.status == SSFEventStatus.SENT:
        return []
    if stream.delivery_method == DeliveryMethods.RISC_PUSH:
        return [ssf_push_event.message(str(event.pk))]
    return []


@actor
def ssf_push_event(event_id: str):
    self: Task = CurrentTask.get_task()
    # TODO: fix me
    # self.save_on_success = False
    event = StreamEvent.objects.filter(pk=event_id).first()
    if not event:
        return
    self.set_uid(event_id)
    if event.status == SSFEventStatus.SENT:
        self.set_status(TaskStatus.SUCCESSFUL)
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
        self.set_status(TaskStatus.SUCCESSFUL)
        return
    except RequestException as exc:
        LOGGER.warning("Failed to send SSF event", exc=exc)
        self.set_status(TaskStatus.ERROR)
        attrs = {}
        if exc.response:
            attrs["response"] = {
                "content": exc.response.text,
                "status": exc.response.status_code,
            }
        self.set_error(
            exc,
            LogEvent(
                _("Failed to send request"),
                log_level="warning",
                # TODO: fix me
                # logger=self.__name__,
                logger=str(self.uid),
                attributes=attrs,
            ),
        )
        # Re-up the expiry of the stream event
        event.expires = now() + timedelta_from_string(event.stream.provider.event_retention)
        event.status = SSFEventStatus.PENDING_FAILED
        event.save()
