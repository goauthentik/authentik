"""Event API tests"""

from datetime import timedelta
from json import loads

from django.urls import reverse
from django.utils.datastructures import MultiValueDict
from django.utils.http import urlencode
from django.utils.timezone import now
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.events.models import (
    Event,
    EventAction,
    Notification,
    NotificationSeverity,
    TransportMode,
)
from authentik.events.utils import model_to_dict
from authentik.lib.generators import generate_id
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

    def test_filter_username_includes_user_model_events(self):
        """User event filtering includes changes made to the user model."""
        target_user = create_test_user()

        for is_active in (False, True):
            with self.subTest(is_active=is_active):
                Event.objects.all().delete()
                response = self.client.patch(
                    reverse("authentik_api:user-detail", kwargs={"pk": target_user.pk}),
                    data={"is_active": is_active},
                )
                self.assertEqual(response.status_code, 200)

                for model in (
                    {
                        "app": "other_app",
                        "model_name": target_user._meta.model_name,
                        "pk": target_user.pk,
                        "name": "unrelated",
                    },
                    {
                        "app": target_user._meta.app_label,
                        "model_name": "other_model",
                        "pk": target_user.pk,
                        "name": "unrelated",
                    },
                ):
                    Event.new(EventAction.MODEL_UPDATED, model=model).save()

                response = self.client.get(
                    reverse("authentik_api:event-list"),
                    data={
                        "username": target_user.username,
                        "action": EventAction.MODEL_UPDATED,
                    },
                )
                self.assertEqual(response.status_code, 200)
                body = loads(response.content)
                self.assertEqual(body["pagination"]["count"], 1)
                self.assertEqual(body["results"][0]["context"]["model"]["pk"], target_user.pk)

    def test_top_n(self):
        """Test top_per_user"""
        event = Event.new(EventAction.AUTHORIZE_APPLICATION)
        event.context["authorized_application"] = {"name": "foo"}
        event.save()  # We save to ensure nothing is un-saveable
        response = self.client.get(
            reverse("authentik_api:event-top-per-user"),
            data={"action": EventAction.AUTHORIZE_APPLICATION},
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            [{"application": {"name": "foo"}, "counted_events": 1, "unique_users": 0}],
        )

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

    def test_volume(self):
        Event.objects.all().delete()
        Event.new(EventAction.LOGIN).set_user(self.user).save()
        evt = Event.new(EventAction.LOGIN).set_user(self.user)
        evt.created = now() - timedelta(days=6)
        evt.save()
        res = self.client.get(
            reverse("authentik_api:event-volume")
            + "?"
            + urlencode(
                {
                    "action": EventAction.LOGIN,
                }
            )
        )
        self.assertEqual(res.status_code, 200)
        data = loads(res.content)
        self.assertEqual(len(data), 1)

    def test_stats(self):
        Event.objects.all().delete()
        Event.new(EventAction.LOGIN).set_user(self.user).save()
        evt = Event.new(EventAction.LOGIN).set_user(self.user)
        evt.created = now() - timedelta(days=6)
        evt.save()
        res = self.client.get(
            reverse("authentik_api:event-stats")
            + "?"
            + urlencode(
                MultiValueDict({"count_steps": ["hours=24", "days=7", "days=240"]}), doseq=True
            )
        )
        self.assertEqual(res.status_code, 200, res.content)
        self.assertJSONEqual(
            res.content, {"unique_users": 1, "count_step": {"hours24": 2, "days7": 2, "days240": 2}}
        )

    def test_stats_invalid(self):
        res = self.client.get(
            reverse("authentik_api:event-stats")
            + "?"
            + urlencode({"count_steps": "24d"}, doseq=True)
        )
        self.assertEqual(res.status_code, 400)
        self.assertJSONEqual(
            res.content,
            {"count_steps": {"0": ["24d is not in the correct format of 'hours=3;minutes=1'."]}},
        )
