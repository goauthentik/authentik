"""Notification transport API tests"""

from django.urls import reverse
from requests_mock import Mocker
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user
from authentik.events.models import NotificationTransport, TransportMode
from authentik.lib.generators import generate_id


class TestTransportsAPI(APITestCase):
    """Test notification transport API"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def test_webhook_test_reports_status(self):
        """Test sending a test notification over a webhook reports the status"""
        transport = NotificationTransport.objects.create(
            name=generate_id(),
            mode=TransportMode.WEBHOOK,
            webhook_url="http://localhost:1234/test",
        )
        with Mocker() as mocker:
            mocker.post("http://localhost:1234/test", text="foo")
            response = self.client.post(
                reverse("authentik_api:notificationtransport-test", kwargs={"pk": transport.pk})
            )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode(), {"messages": ["200"]})

    def test_webhook_slack_test_reports_status(self):
        """Test sending a test notification over a slack webhook reports the status"""
        transport = NotificationTransport.objects.create(
            name=generate_id(),
            mode=TransportMode.WEBHOOK_SLACK,
            webhook_url="http://localhost:1234/test",
        )
        with Mocker() as mocker:
            mocker.post("http://localhost:1234/test", text="foo")
            response = self.client.post(
                reverse("authentik_api:notificationtransport-test", kwargs={"pk": transport.pk})
            )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode(), {"messages": ["200"]})

    def test_webhook_test_reports_error(self):
        """Test sending a test notification over a failing webhook reports the error"""
        transport = NotificationTransport.objects.create(
            name=generate_id(),
            mode=TransportMode.WEBHOOK,
            webhook_url="http://localhost:1234/test",
        )
        with Mocker() as mocker:
            mocker.post(
                "http://localhost:1234/test",
                status_code=500,
                reason="Internal Server Error",
                text="foo",
            )
            response = self.client.post(
                reverse("authentik_api:notificationtransport-test", kwargs={"pk": transport.pk})
            )
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json(),
            "500 Server Error: Internal Server Error for url: http://localhost:1234/test",
        )
