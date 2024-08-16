from celery import group
from requests.exceptions import RequestException

from authentik.enterprise.providers.ssf.models import DeliveryMethods, EventTypes, Stream
from authentik.lib.utils.http import get_http_session
from authentik.root.celery import CELERY_APP

session = get_http_session()


@CELERY_APP.task(bind=True)
def send_ssf_event(event_type: EventTypes, subject):
    tasks = []
    for stream in Stream.objects.filter(
        delivery_method=DeliveryMethods.RISC_PUSH,
        events_requested__in=[event_type],
    ):
        tasks.append(ssf_push_request.si(stream.endpoint_url, {}))
    main_task = group(*tasks)
    main_task()


@CELERY_APP.task(bind=True, autoretry=True, autoretry_for=(RequestException,), retry_backoff=True)
def ssf_push_request(endpoint_url: str, data: dict):
    response = session.post(endpoint_url, data)
    response.raise_for_status()
