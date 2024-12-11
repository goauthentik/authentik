from celery import group
from requests.exceptions import RequestException

from authentik.enterprise.providers.ssf.models import DeliveryMethods, EventTypes, Stream
from authentik.lib.utils.http import get_http_session
from authentik.root.celery import CELERY_APP

session = get_http_session()


@CELERY_APP.task(bind=True)
def send_ssf_event(event_type: EventTypes, data: dict):
    tasks = []
    for stream in Stream.objects.filter(events_requested__in=[event_type]):
        tasks.append(send_single_ssf_event.si(str(stream.uuid), data))
    main_task = group(*tasks)
    main_task()


@CELERY_APP.task(bind=True, autoretry=True, autoretry_for=(RequestException,), retry_backoff=True)
def send_single_ssf_event(self, stream_id: str, data: dict):
    stream = Stream.objects.filter(pk=stream_id).first()
    if not stream:
        return
    if stream.delivery_method == DeliveryMethods.RISC_PUSH:
        ssf_push_request.delay(stream_id, data)


@CELERY_APP.task(bind=True, autoretry=True, autoretry_for=(RequestException,), retry_backoff=True)
def ssf_push_request(self, stream_id: str, data: dict):
    stream = Stream.objects.filter(pk=stream_id).first()
    if not stream:
        return
    response = session.post(
        stream.endpoint_url,
        data=stream.encode(data),
        headers={"Content-Type": "application/secevent+jwt", "Accept": "application/json"},
    )
    response.raise_for_status()
