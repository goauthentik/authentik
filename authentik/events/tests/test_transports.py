"""transport tests"""

from unittest.mock import PropertyMock, patch

from django.core import mail
from django.core.mail.backends.locmem import EmailBackend
from django.test import TestCase
from django.urls import reverse
from requests_mock import Mocker

from authentik import authentik_full_version
from authentik.core.tests.utils import create_test_admin_user
from authentik.events.api.notification_transports import NotificationTransportSerializer
from authentik.events.models import (
    Event,
    Notification,
    NotificationSeverity,
    NotificationTransport,
    NotificationWebhookMapping,
    TransportMode,
)
from authentik.lib.generators import generate_id
from authentik.stages.email.models import get_template_choices


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
        mapping_body = NotificationWebhookMapping.objects.create(
            name=generate_id(), expression="return request.user"
        )
        mapping_headers = NotificationWebhookMapping.objects.create(
            name=generate_id(), expression="""return {"foo": "bar"}"""
        )
        transport: NotificationTransport = NotificationTransport.objects.create(
            name=generate_id(),
            mode=TransportMode.WEBHOOK,
            webhook_url="http://localhost:1234/test",
            webhook_mapping_body=mapping_body,
            webhook_mapping_headers=mapping_headers,
        )
        with Mocker() as mocker:
            mocker.post("http://localhost:1234/test")
            transport.send(self.notification)
            self.assertEqual(mocker.call_count, 1)
            self.assertEqual(mocker.request_history[0].method, "POST")
            self.assertEqual(mocker.request_history[0].headers["foo"], "bar")
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
                            "footer": f"authentik {authentik_full_version()}",
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

    def test_transport_email_custom_template(self):
        """Test email transport with custom template"""
        transport: NotificationTransport = NotificationTransport.objects.create(
            name=generate_id(),
            mode=TransportMode.EMAIL,
            email_template="email/event_notification.html",
        )
        with patch(
            "authentik.stages.email.models.EmailStage.backend_class",
            PropertyMock(return_value=EmailBackend),
        ):
            transport.send(self.notification)
            self.assertEqual(len(mail.outbox), 1)
            self.assertIn(self.notification.body, mail.outbox[0].alternatives[0][0])

    def test_transport_email_custom_subject_prefix(self):
        """Test email transport with custom subject prefix"""
        transport: NotificationTransport = NotificationTransport.objects.create(
            name=generate_id(),
            mode=TransportMode.EMAIL,
            email_subject_prefix="[CUSTOM] ",
        )
        with patch(
            "authentik.stages.email.models.EmailStage.backend_class",
            PropertyMock(return_value=EmailBackend),
        ):
            transport.send(self.notification)
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].subject, "[CUSTOM] custom_foo")

    def test_transport_email_validation(self):
        """Test email transport template validation"""

        # Test valid template
        serializer = NotificationTransportSerializer(
            data={
                "name": generate_id(),
                "mode": TransportMode.EMAIL,
                "email_template": "email/event_notification.html",
            }
        )
        self.assertTrue(serializer.is_valid())

        # Test invalid template - should fail due to choices validation
        serializer = NotificationTransportSerializer(
            data={
                "name": generate_id(),
                "mode": TransportMode.EMAIL,
                "email_template": "invalid/template.html",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("email_template", serializer.errors)

    def test_templates_api_endpoint(self):
        """Test templates API endpoint returns valid templates"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("authentik_api:emailstage-templates"))
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIsInstance(data, list)

        # Check that we have at least the default templates
        template_names = [item["name"] for item in data]
        self.assertIn("email/event_notification.html", template_names)

        # Verify all templates are valid choices
        valid_choices = dict(get_template_choices())
        for template in data:
            self.assertIn(template["name"], valid_choices)
            self.assertEqual(template["description"], valid_choices[template["name"]])
