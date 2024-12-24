from celery import group
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


@CELERY_APP.task(bind=True)
def send_ssf_event(event_type: EventTypes, data: dict):
    tasks = []
    for stream in Stream.objects.filter(events_requested__in=[event_type]):
        event = stream.new_event(
            type=event_type,
        )
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
