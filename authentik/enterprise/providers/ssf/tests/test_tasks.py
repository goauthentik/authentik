from jwt import decode_complete
from requests_mock import Mocker
from rest_framework.test import APITestCase

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_cert
from authentik.enterprise.providers.ssf.models import (
    DeliveryMethods,
    EventTypes,
    SSFProvider,
    Stream,
    StreamStatus,
)
from authentik.enterprise.providers.ssf.tasks import send_ssf_event
from authentik.lib.generators import generate_id
from authentik.tasks.models import TaskLog


class TestTasks(APITestCase):
    def setUp(self):
        self.application = Application.objects.create(name=generate_id(), slug=generate_id())
        self.provider = SSFProvider.objects.create(
            name=generate_id(),
            signing_key=create_test_cert(),
            backchannel_application=self.application,
        )

    def test_push_simple(self):
        stream = Stream.objects.create(
            provider=self.provider,
            delivery_method=DeliveryMethods.RFC_PUSH,
            endpoint_url="http://localhost/ssf-push",
        )
        event_data = stream.prepare_event_payload(
            EventTypes.SET_VERIFICATION,
            {},
            sub_id={"format": "opaque", "id": str(stream.uuid)},
        )
        with Mocker() as mocker:
            mocker.post("http://localhost/ssf-push", status_code=202)
            send_ssf_event.send_with_options(
                args=(stream.pk, event_data), rel_obj=stream.provider
            ).get_result(block=True, timeout=1)
        self.assertEqual(
            mocker.request_history[0].headers["Content-Type"], "application/secevent+jwt"
        )
        jwt = decode_complete(mocker.request_history[0].body, options={"verify_signature": False})
        self.assertEqual(jwt["header"]["typ"], "secevent+jwt")
        self.assertEqual(jwt["payload"]["events"][EventTypes.SET_VERIFICATION], {})

    def test_push_auth(self):
        auth = generate_id()
        stream = Stream.objects.create(
            provider=self.provider,
            delivery_method=DeliveryMethods.RFC_PUSH,
            endpoint_url="http://localhost/ssf-push",
            authorization_header=auth,
        )
        event_data = stream.prepare_event_payload(
            EventTypes.SET_VERIFICATION,
            {},
            sub_id={"format": "opaque", "id": str(stream.uuid)},
        )
        with Mocker() as mocker:
            mocker.post("http://localhost/ssf-push", status_code=202)
            send_ssf_event.send_with_options(
                args=(stream.pk, event_data), rel_obj=stream.provider
            ).get_result(block=True, timeout=1)
        self.assertEqual(mocker.request_history[0].headers["Authorization"], auth)
        self.assertEqual(
            mocker.request_history[0].headers["Content-Type"], "application/secevent+jwt"
        )
        jwt = decode_complete(mocker.request_history[0].body, options={"verify_signature": False})
        self.assertEqual(jwt["header"]["typ"], "secevent+jwt")
        self.assertEqual(jwt["payload"]["events"][EventTypes.SET_VERIFICATION], {})

    def test_push_stream_disable(self):
        auth = generate_id()
        stream = Stream.objects.create(
            provider=self.provider,
            delivery_method=DeliveryMethods.RFC_PUSH,
            endpoint_url="http://localhost/ssf-push",
            authorization_header=auth,
            status=StreamStatus.DISABLED_DELETED,
        )
        event_data = stream.prepare_event_payload(
            EventTypes.SET_VERIFICATION,
            {},
            sub_id={"format": "opaque", "id": str(stream.uuid)},
        )
        with Mocker() as mocker:
            mocker.post("http://localhost/ssf-push", status_code=202)
            send_ssf_event.send_with_options(
                args=(stream.pk, event_data), rel_obj=stream.provider
            ).get_result(block=True, timeout=1)
        jwt = decode_complete(mocker.request_history[0].body, options={"verify_signature": False})
        self.assertEqual(jwt["header"]["typ"], "secevent+jwt")
        self.assertEqual(jwt["payload"]["events"][EventTypes.SET_VERIFICATION], {})
        self.assertFalse(Stream.objects.filter(pk=stream.pk).exists())

    def test_push_error(self):
        stream = Stream.objects.create(
            provider=self.provider,
            delivery_method=DeliveryMethods.RFC_PUSH,
            endpoint_url="http://localhost/ssf-push",
        )
        event_data = stream.prepare_event_payload(
            EventTypes.SET_VERIFICATION,
            {},
            sub_id={"format": "opaque", "id": str(stream.uuid)},
        )
        with Mocker() as mocker:
            mocker.post("http://localhost/ssf-push", text="error", status_code=400)
            send_ssf_event.send_with_options(
                args=(stream.pk, event_data), rel_obj=stream.provider
            ).get_result(block=True, timeout=1)
        logs = (
            TaskLog.objects.filter(task__actor_name=send_ssf_event.actor_name)
            .order_by("timestamp")
            .filter(event="Failed to send request")
            .first()
        )
        self.assertEqual(logs.attributes, {"response": {"status": 400, "content": "error"}})
