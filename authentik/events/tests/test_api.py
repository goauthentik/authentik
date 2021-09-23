"""Event API tests"""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import User
from authentik.events.models import (
    Event,
    EventAction,
    Notification,
    NotificationSeverity,
    TransportMode,
)


class TestEventsAPI(APITestCase):
    """Test Event API"""

    def setUp(self) -> None:
        self.user = User.objects.get(username="akadmin")
        self.client.force_login(self.user)

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
