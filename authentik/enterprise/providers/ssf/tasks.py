from celery import group
from django.http import HttpRequest
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from requests.exceptions import RequestException
from structlog.stdlib import get_logger

from authentik.enterprise.providers.ssf.models import (
    DeliveryMethods,
    EventTypes,
    SSFEventStatus,
    Stream,
    StreamEvent,
)
from authentik.events.logs import LogEvent
from authentik.events.models import TaskStatus
from authentik.events.system_tasks import SystemTask
from authentik.lib.utils.http import get_http_session
from authentik.lib.utils.time import timedelta_from_string
from authentik.root.celery import CELERY_APP

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
        data.setdefault("txn", request.request_id)
    for stream in Stream.objects.filter(**stream_filter):
        event_data = stream.prepare_event_payload(event_type, data, **extra_data)
        payload.append((str(stream.uuid), event_data))
    return _send_ssf_event.delay(payload)


@CELERY_APP.task()
def _send_ssf_event(event_data: list[tuple[str, dict]]):
    tasks = []
    for stream, data in event_data:
        event = StreamEvent.objects.create(**data)
        tasks.extend(send_single_ssf_event(stream, str(event.uuid)))
    main_task = group(*tasks)
    main_task()


def send_single_ssf_event(stream_id: str, evt_id: str):
    stream = Stream.objects.filter(pk=stream_id).first()
    if not stream:
        return
    event = StreamEvent.objects.filter(pk=evt_id).first()
    if not event:
        return
    if event.status == SSFEventStatus.SENT:
        return
    if stream.delivery_method == DeliveryMethods.RISC_PUSH:
        return [ssf_push_event.si(str(event.pk))]
    return []


@CELERY_APP.task(bind=True, base=SystemTask)
def ssf_push_event(self: SystemTask, event_id: str):
    self.save_on_success = False
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
                logger=self.__name__,
                attributes=attrs,
            ),
        )
        # Re-up the expiry of the stream event
        event.expires = now() + timedelta_from_string(event.stream.provider.event_retention)
        event.status = SSFEventStatus.PENDING_FAILED
        event.save()
