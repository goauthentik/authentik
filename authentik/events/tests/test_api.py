"""Event API tests"""

from json import loads

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user
from authentik.crypto.generators import generate_id
from authentik.events.models import (
    Event,
    EventAction,
    Notification,
    NotificationSeverity,
    TransportMode,
)
from authentik.events.utils import model_to_dict
from authentik.providers.oauth2.models import OAuth2Provider


class TestEventsAPI(APITestCase):
    """Test Event API"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def test_filter_model_pk_int(self):
        """Test event list with context_model_pk and integer PKs"""
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
        )
        event = Event.new(EventAction.MODEL_CREATED, model=model_to_dict(provider))
        event.save()
        response = self.client.get(
            reverse("authentik_api:event-list"),
            data={
                "context_model_pk": provider.pk,
                "context_model_app": "authentik_providers_oauth2",
                "context_model_name": "oauth2provider",
            },
        )
        self.assertEqual(response.status_code, 200)
        body = loads(response.content)
        self.assertEqual(body["pagination"]["count"], 1)

    def test_top_n(self):
        """Test top_per_user"""
        event = Event.new(EventAction.AUTHORIZE_APPLICATION)
        event.save()  # We save to ensure nothing is un-saveable
        response = self.client.get(
            reverse("authentik_api:event-top-per-user"),
            data={"filter_action": EventAction.AUTHORIZE_APPLICATION},
        )
        self.assertEqual(response.status_code, 200)

    def test_actions(self):
        """Test actions"""
        response = self.client.get(
            reverse("authentik_api:event-actions"),
        )
        self.assertEqual(response.status_code, 200)

    def test_notifications(self):
        """Test notifications"""
        notification = Notification.objects.create(
            user=self.user, severity=NotificationSeverity.ALERT, body="", seen=False
        )
        self.client.post(
            reverse("authentik_api:notification-mark-all-seen"),
        )
        notification.refresh_from_db()
        self.assertTrue(notification.seen)

    def test_transport(self):
        """Test transport API"""
        response = self.client.post(
            reverse("authentik_api:notificationtransport-list"),
            data={
                "name": "foo-with",
                "mode": TransportMode.WEBHOOK,
                "webhook_url": "http://foo.com",
            },
        )
        self.assertEqual(response.status_code, 201)
        response = self.client.post(
            reverse("authentik_api:notificationtransport-list"),
            data={
                "name": "foo-without",
                "mode": TransportMode.WEBHOOK,
            },
        )
        self.assertEqual(response.status_code, 400)
