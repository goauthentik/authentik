"""Test Users Panic Button API"""

from json import loads
from unittest.mock import patch

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import AuthenticatedSession, Session
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.events.models import Event, EventAction
from authentik.lib.generators import generate_id
from authentik.tenants.models import Tenant


class TestUsersPanicButtonAPI(APITestCase):
    """Test Users Panic Button API"""

    def setUp(self) -> None:
        self.admin = create_test_admin_user()
        self.user = create_test_user()
        self.user.email = f"{generate_id()}@test.com"
        self.user.save()
        self.tenant = Tenant.objects.first()
        self.tenant.panic_button_enabled = True
        self.tenant.save()

    def test_panic_button_success(self):
        """Test successful panic button trigger"""
        self.client.force_login(self.admin)
        old_password = self.user.password

        with patch("authentik.events.tasks.panic_button_notification.send_with_options") as mock:
            response = self.client.post(
                reverse("authentik_api:user-panic-button", kwargs={"pk": self.user.pk}),
                data={"reason": "Compromised account"},
            )

        self.assertEqual(response.status_code, 204)

        # Verify user was deactivated and password changed
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertNotEqual(self.user.password, old_password)

        # Verify notification task was called
        mock.assert_called_once()
        call_args = mock.call_args
        self.assertEqual(call_args.kwargs["args"][0], self.user.pk)
        self.assertEqual(call_args.kwargs["args"][1], self.admin.pk)
        self.assertEqual(call_args.kwargs["args"][2], "Compromised account")

    def test_panic_button_creates_event(self):
        """Test that panic button creates an event"""
        self.client.force_login(self.admin)
        Event.objects.all().delete()

        with patch("authentik.events.tasks.panic_button_notification.send_with_options"):
            response = self.client.post(
                reverse("authentik_api:user-panic-button", kwargs={"pk": self.user.pk}),
                data={"reason": "Security incident"},
            )

        self.assertEqual(response.status_code, 204)

        # Verify event was created
        event = Event.objects.filter(action=EventAction.PANIC_BUTTON_TRIGGERED).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.context["reason"], "Security incident")
        self.assertEqual(event.context["affected_user"], self.user.username)
        self.assertEqual(event.context["triggered_by"], self.admin.username)

    def test_panic_button_deletes_sessions(self):
        """Test that panic button deletes user sessions"""
        self.client.force_login(self.admin)

        # Create a session for the target user
        session_id = generate_id()
        session = Session.objects.create(
            session_key=session_id,
            last_ip="127.0.0.1",
            last_user_agent="test",
        )
        AuthenticatedSession.objects.create(session=session, user=self.user)

        with patch("authentik.events.tasks.panic_button_notification.send_with_options"):
            response = self.client.post(
                reverse("authentik_api:user-panic-button", kwargs={"pk": self.user.pk}),
                data={"reason": "Session hijack"},
            )

        self.assertEqual(response.status_code, 204)

        # Verify session was deleted
        self.assertFalse(Session.objects.filter(session_key=session_id).exists())

    def test_panic_button_disabled(self):
        """Test panic button when feature is disabled"""
        self.tenant.panic_button_enabled = False
        self.tenant.save()
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("authentik_api:user-panic-button", kwargs={"pk": self.user.pk}),
            data={"reason": "Test"},
        )

        self.assertEqual(response.status_code, 400)
        body = loads(response.content)
        self.assertIn("Panic button feature is disabled", body["non_field_errors"][0])

    def test_panic_button_self_trigger_denied(self):
        """Test that users cannot trigger panic button on themselves"""
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("authentik_api:user-panic-button", kwargs={"pk": self.admin.pk}),
            data={"reason": "Self test"},
        )

        self.assertEqual(response.status_code, 400)
        body = loads(response.content)
        self.assertIn("Cannot trigger panic button on yourself", body["non_field_errors"][0])

    def test_panic_button_requires_reason(self):
        """Test that reason field is required"""
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("authentik_api:user-panic-button", kwargs={"pk": self.user.pk}),
            data={},
        )

        self.assertEqual(response.status_code, 400)
        body = loads(response.content)
        self.assertIn("reason", body)

    def test_panic_button_notification_overrides(self):
        """Test panic button with notification overrides"""
        self.client.force_login(self.admin)

        with patch("authentik.events.tasks.panic_button_notification.send_with_options") as mock:
            response = self.client.post(
                reverse("authentik_api:user-panic-button", kwargs={"pk": self.user.pk}),
                data={
                    "reason": "Test",
                    "notify_user": False,
                    "notify_admins": True,
                    "notify_security": True,
                },
            )

        self.assertEqual(response.status_code, 204)
        call_args = mock.call_args.kwargs["args"]
        self.assertFalse(call_args[3])  # notify_user
        self.assertTrue(call_args[4])  # notify_admins
        self.assertTrue(call_args[5])  # notify_security

    def test_panic_button_uses_tenant_defaults(self):
        """Test that panic button uses tenant notification defaults when not overridden"""
        self.tenant.panic_button_notify_user = False
        self.tenant.panic_button_notify_admins = True
        self.tenant.panic_button_notify_security = True
        self.tenant.save()
        self.client.force_login(self.admin)

        with patch("authentik.events.tasks.panic_button_notification.send_with_options") as mock:
            response = self.client.post(
                reverse("authentik_api:user-panic-button", kwargs={"pk": self.user.pk}),
                data={"reason": "Test"},
            )

        self.assertEqual(response.status_code, 204)
        call_args = mock.call_args.kwargs["args"]
        self.assertFalse(call_args[3])  # notify_user (from tenant default)
        self.assertTrue(call_args[4])  # notify_admins (from tenant default)
        self.assertTrue(call_args[5])  # notify_security (from tenant default)

    def test_panic_button_unauthenticated(self):
        """Test panic button requires authentication"""
        response = self.client.post(
            reverse("authentik_api:user-panic-button", kwargs={"pk": self.user.pk}),
            data={"reason": "Test"},
        )

        self.assertEqual(response.status_code, 403)

    def test_panic_button_non_admin(self):
        """Test panic button requires admin permissions"""
        regular_user = create_test_user()
        self.client.force_login(regular_user)

        response = self.client.post(
            reverse("authentik_api:user-panic-button", kwargs={"pk": self.user.pk}),
            data={"reason": "Test"},
        )

        self.assertEqual(response.status_code, 403)


class TestUsersPanicButtonBulkAPI(APITestCase):
    """Test Users Panic Button Bulk API"""

    def setUp(self) -> None:
        self.admin = create_test_admin_user()
        self.user1 = create_test_user()
        self.user1.email = f"{generate_id()}@test.com"
        self.user1.save()
        self.user2 = create_test_user()
        self.user2.email = f"{generate_id()}@test.com"
        self.user2.save()
        self.tenant = Tenant.objects.first()
        self.tenant.panic_button_enabled = True
        self.tenant.save()

    def test_panic_button_bulk_success(self):
        """Test successful bulk panic button trigger"""
        self.client.force_login(self.admin)

        with patch("authentik.events.tasks.panic_button_notification.send_with_options") as mock:
            response = self.client.post(
                reverse("authentik_api:user-panic-button-bulk"),
                data={
                    "users": [self.user1.pk, self.user2.pk],
                    "reason": "Bulk security incident",
                },
                format="json",
            )

        self.assertEqual(response.status_code, 204)

        # Verify both users were deactivated
        self.user1.refresh_from_db()
        self.user2.refresh_from_db()
        self.assertFalse(self.user1.is_active)
        self.assertFalse(self.user2.is_active)

        # Verify notification task was called for each user
        self.assertEqual(mock.call_count, 2)

    def test_panic_button_bulk_skips_self(self):
        """Test that bulk panic button skips the requesting user"""
        self.client.force_login(self.admin)

        with patch("authentik.events.tasks.panic_button_notification.send_with_options") as mock:
            response = self.client.post(
                reverse("authentik_api:user-panic-button-bulk"),
                data={
                    "users": [self.user1.pk, self.admin.pk],
                    "reason": "Test",
                },
                format="json",
            )

        self.assertEqual(response.status_code, 204)

        # Verify only user1 was deactivated, admin should remain active
        self.user1.refresh_from_db()
        self.admin.refresh_from_db()
        self.assertFalse(self.user1.is_active)
        self.assertTrue(self.admin.is_active)

        # Should only be called once (for user1)
        self.assertEqual(mock.call_count, 1)

    def test_panic_button_bulk_disabled(self):
        """Test bulk panic button when feature is disabled"""
        self.tenant.panic_button_enabled = False
        self.tenant.save()
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("authentik_api:user-panic-button-bulk"),
            data={
                "users": [self.user1.pk],
                "reason": "Test",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        body = loads(response.content)
        self.assertIn("Panic button feature is disabled", body["non_field_errors"][0])

    def test_panic_button_bulk_requires_users(self):
        """Test that users field is required"""
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("authentik_api:user-panic-button-bulk"),
            data={"reason": "Test"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        body = loads(response.content)
        self.assertIn("users", body)

    def test_panic_button_bulk_requires_reason(self):
        """Test that reason field is required"""
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("authentik_api:user-panic-button-bulk"),
            data={"users": [self.user1.pk]},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        body = loads(response.content)
        self.assertIn("reason", body)

    def test_panic_button_bulk_notification_overrides(self):
        """Test bulk panic button with notification overrides"""
        self.client.force_login(self.admin)

        with patch("authentik.events.tasks.panic_button_notification.send_with_options") as mock:
            response = self.client.post(
                reverse("authentik_api:user-panic-button-bulk"),
                data={
                    "users": [self.user1.pk],
                    "reason": "Test",
                    "notify_user": False,
                    "notify_admins": True,
                    "notify_security": False,
                },
                format="json",
            )

        self.assertEqual(response.status_code, 204)
        call_args = mock.call_args.kwargs["args"]
        self.assertFalse(call_args[3])  # notify_user
        self.assertTrue(call_args[4])  # notify_admins
        self.assertFalse(call_args[5])  # notify_security

    def test_panic_button_bulk_unauthenticated(self):
        """Test bulk panic button requires authentication"""
        response = self.client.post(
            reverse("authentik_api:user-panic-button-bulk"),
            data={
                "users": [self.user1.pk],
                "reason": "Test",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_panic_button_bulk_non_admin(self):
        """Test bulk panic button requires admin permissions"""
        regular_user = create_test_user()
        self.client.force_login(regular_user)

        response = self.client.post(
            reverse("authentik_api:user-panic-button-bulk"),
            data={
                "users": [self.user1.pk],
                "reason": "Test",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_panic_button_bulk_empty_users(self):
        """Test bulk panic button with empty users list"""
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("authentik_api:user-panic-button-bulk"),
            data={
                "users": [],
                "reason": "Test",
            },
            format="json",
        )

        # Empty list should still be accepted and return success
        self.assertEqual(response.status_code, 204)

    def test_panic_button_bulk_creates_events(self):
        """Test that bulk panic button creates events for each user"""
        self.client.force_login(self.admin)
        Event.objects.all().delete()

        with patch("authentik.events.tasks.panic_button_notification.send_with_options"):
            response = self.client.post(
                reverse("authentik_api:user-panic-button-bulk"),
                data={
                    "users": [self.user1.pk, self.user2.pk],
                    "reason": "Bulk test",
                },
                format="json",
            )

        self.assertEqual(response.status_code, 204)

        # Verify events were created for each user
        events = Event.objects.filter(action=EventAction.PANIC_BUTTON_TRIGGERED)
        self.assertEqual(events.count(), 2)

        usernames = {event.context["affected_user"] for event in events}
        self.assertIn(self.user1.username, usernames)
        self.assertIn(self.user2.username, usernames)
