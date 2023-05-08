"""transport tests"""
from unittest.mock import PropertyMock, patch

from django.core import mail
from django.core.mail.backends.locmem import EmailBackend
from django.test import TestCase
from requests_mock import Mocker

from authentik import get_full_version
from authentik.core.tests.utils import create_test_admin_user
from authentik.events.models import (
    Event,
    Notification,
    NotificationSeverity,
    NotificationTransport,
    NotificationWebhookMapping,
    TransportMode,
)
from authentik.lib.generators import generate_id


class TestEventTransports(TestCase):
    """Test Event Transports"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()
        self.event = Event.new("foo", "testing", foo="bar,").set_user(self.user)
        self.event.save()
        self.notification = Notification.objects.create(
            severity=NotificationSeverity.ALERT,
            body="foo",
            event=self.event,
            user=self.user,
        )

    def test_transport_webhook(self):
        """Test webhook transport"""
        transport: NotificationTransport = NotificationTransport.objects.create(
            name=generate_id(),
            mode=TransportMode.WEBHOOK,
            webhook_url="http://localhost:1234/test",
        )
        with Mocker() as mocker:
            mocker.post("http://localhost:1234/test")
            transport.send(self.notification)
            self.assertEqual(mocker.call_count, 1)
            self.assertEqual(mocker.request_history[0].method, "POST")
            self.assertJSONEqual(
                mocker.request_history[0].body.decode(),
                {
                    "body": "foo",
                    "severity": "alert",
                    "user_email": self.user.email,
                    "user_username": self.user.username,
                    "event_user_email": self.user.email,
                    "event_user_username": self.user.username,
                },
            )

    def test_transport_webhook_mapping(self):
        """Test webhook transport with custom mapping"""
        mapping = NotificationWebhookMapping.objects.create(
            name=generate_id(), expression="return request.user"
        )
        transport: NotificationTransport = NotificationTransport.objects.create(
            name=generate_id(),
            mode=TransportMode.WEBHOOK,
            webhook_url="http://localhost:1234/test",
            webhook_mapping=mapping,
        )
        with Mocker() as mocker:
            mocker.post("http://localhost:1234/test")
            transport.send(self.notification)
            self.assertEqual(mocker.call_count, 1)
            self.assertEqual(mocker.request_history[0].method, "POST")
            self.assertJSONEqual(
                mocker.request_history[0].body.decode(),
                {"email": self.user.email, "pk": self.user.pk, "username": self.user.username},
            )

    def test_transport_webhook_slack(self):
        """Test webhook transport (slack)"""
        transport: NotificationTransport = NotificationTransport.objects.create(
            name=generate_id(),
            mode=TransportMode.WEBHOOK_SLACK,
            webhook_url="http://localhost:1234/test",
        )
        with Mocker() as mocker:
            mocker.post("http://localhost:1234/test")
            transport.send(self.notification)
            self.assertEqual(mocker.call_count, 1)
            self.assertEqual(mocker.request_history[0].method, "POST")
            self.assertJSONEqual(
                mocker.request_history[0].body.decode(),
                {
                    "username": "authentik",
                    "icon_url": "https://goauthentik.io/img/icon.png",
                    "attachments": [
                        {
                            "author_name": "authentik",
                            "author_link": "https://goauthentik.io",
                            "author_icon": "https://goauthentik.io/img/icon.png",
                            "title": "custom_foo",
                            "color": "#fd4b2d",
                            "fields": [
                                {"title": "Severity", "value": "alert", "short": True},
                                {
                                    "title": "Dispatched for user",
                                    "value": self.user.username,
                                    "short": True,
                                },
                                {"short": True, "title": "Event user", "value": self.user.username},
                                {"title": "foo", "value": "bar,"},
                            ],
                            "footer": f"authentik {get_full_version()}",
                        }
                    ],
                },
            )

    def test_transport_email(self):
        """Test email transport"""
        transport: NotificationTransport = NotificationTransport.objects.create(
            name=generate_id(),
            mode=TransportMode.EMAIL,
        )
        with patch(
            "authentik.stages.email.models.EmailStage.backend_class",
            PropertyMock(return_value=EmailBackend),
        ):
            transport.send(self.notification)
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].subject, "authentik Notification: custom_foo")
            self.assertIn(self.notification.body, mail.outbox[0].alternatives[0][0])
