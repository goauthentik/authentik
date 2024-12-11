from celery import group
from django.http import HttpRequest
from requests.exceptions import RequestException

from authentik.enterprise.providers.ssf.models import (
    DeliveryMethods,
    EventTypes,
    SSFEventStatus,
    Stream,
    StreamEvent,
)
from authentik.lib.utils.http import get_http_session
from authentik.root.celery import CELERY_APP

session = get_http_session()


def send_ssf_event(
    event_type: EventTypes,
    request: HttpRequest,
    data: dict,
    stream_filter: dict | None = None,
    **extra_data,
):
    """Wrapper to send an SSF event to multiple streams"""
    payload = []
    if not stream_filter:
        stream_filter = {}
    stream_filter["events_requested__in"] = [event_type]
    for stream in Stream.objects.filter(**stream_filter):
        event_data = stream.prepare_event_payload(event_type, request, data, **extra_data)
        payload.append((str(stream.uuid), event_data))
    return _send_ssf_event.delay(payload)


@CELERY_APP.task(bind=True)
def _send_ssf_event(event_data: list[tuple[str, dict]]):
    tasks = []
    for stream, data in event_data:
        event = StreamEvent.objects.create(**data)
        tasks.append(send_single_ssf_event.si(str(stream.uuid), str(event.id)))
    main_task = group(*tasks)
    main_task()


@CELERY_APP.task(bind=True, autoretry=True, autoretry_for=(RequestException,), retry_backoff=True)
def send_single_ssf_event(self, stream_id: str, evt_id: str):
    stream = Stream.objects.filter(pk=stream_id).first()
    if not stream:
        return
    event = StreamEvent.objects.filter(pk=evt_id).first()
    if not event:
        return
    if event.status == SSFEventStatus.SENT:
        return
    if stream.delivery_method == DeliveryMethods.RISC_PUSH:
        ssf_push_request(event)
    event.status = SSFEventStatus.SENT
    event.save()


def ssf_push_request(event: StreamEvent):
    response = session.post(
        event.stream.endpoint_url,
        data=event.stream.encode(event.payload),
        headers={"Content-Type": "application/secevent+jwt", "Accept": "application/json"},
    )
    response.raise_for_status()
