from datetime import timedelta

from django.apps import apps
from django.urls import reverse
from django.utils.timezone import now
from rest_framework.test import APITestCase

from authentik.core.models import AuthenticatedSession, Session, Token, TokenIntents, User
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.enterprise.lifecycle.models import (
    OffboardingAction,
    OffboardingStatus,
    UserOffboarding,
)
from authentik.enterprise.lifecycle.offboarding import offboard_user
from authentik.enterprise.lifecycle.tasks import execute_due_offboardings, execute_offboarding
from authentik.enterprise.reports.tests.utils import patch_license
from authentik.events.models import Event, EventAction
from authentik.lib.generators import generate_id


def _add_session(user: User) -> AuthenticatedSession:
    session = Session.objects.create(
        session_key=generate_id(), last_ip="255.255.255.255", last_user_agent=""
    )
    return AuthenticatedSession.objects.create(session=session, user=user)


def _add_token(user: User) -> Token:
    return Token.objects.create(identifier=generate_id(), user=user, intent=TokenIntents.INTENT_API)


class TestOffboardingService(APITestCase):
    def setUp(self):
        self.user = create_test_user()

    def test_deactivate_revokes_access(self):
        _add_session(self.user)
        _add_token(self.user)
        offboard_user(self.user, OffboardingAction.DEACTIVATE)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertFalse(AuthenticatedSession.objects.filter(user=self.user).exists())
        self.assertFalse(Token.objects.filter(user=self.user).exists())

    def test_delete_removes_user(self):
        pk = self.user.pk
        offboard_user(self.user, OffboardingAction.DELETE)
        self.assertFalse(User.objects.filter(pk=pk).exists())

    def test_revoke_toggles_off(self):
        _add_session(self.user)
        _add_token(self.user)
        offboard_user(
            self.user,
            OffboardingAction.DEACTIVATE,
            revoke_sessions=False,
            revoke_tokens=False,
        )
        self.assertTrue(AuthenticatedSession.objects.filter(user=self.user).exists())
        self.assertTrue(Token.objects.filter(user=self.user).exists())


class TestOffboardingSweeper(APITestCase):
    def setUp(self):
        self.user = create_test_user()

    def test_due_offboarding_executed(self):
        offboarding = UserOffboarding.objects.create(
            user=self.user,
            scheduled_for=now() - timedelta(minutes=1),
            action=OffboardingAction.DEACTIVATE,
        )
        execute_offboarding(str(offboarding.pk))
        offboarding.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(offboarding.status, OffboardingStatus.COMPLETED)
        self.assertIsNotNone(offboarding.executed_on)
        self.assertFalse(self.user.is_active)

    def test_audit_event_attributed_to_initiator(self):
        """The audit event names the admin who scheduled it, not the offboarded user."""
        admin = create_test_admin_user()
        offboarding = UserOffboarding.objects.create(
            user=self.user,
            scheduled_for=now() - timedelta(minutes=1),
            action=OffboardingAction.DEACTIVATE,
            created_by=admin,
        )
        execute_offboarding(str(offboarding.pk))
        event = Event.objects.filter(action=EventAction.USER_OFFBOARDED).latest("created")
        self.assertEqual(event.user.get("pk"), admin.pk)
        self.assertNotEqual(event.user.get("pk"), self.user.pk)
        self.assertEqual(event.context.get("user_pk"), self.user.pk)

    def test_future_offboarding_not_picked_up(self):
        offboarding = UserOffboarding.objects.create(
            user=self.user,
            scheduled_for=now() + timedelta(days=1),
            action=OffboardingAction.DEACTIVATE,
        )
        execute_due_offboardings()
        offboarding.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(offboarding.status, OffboardingStatus.PENDING)
        self.assertTrue(self.user.is_active)


@patch_license
class TestOffboardingAPI(APITestCase):
    def setUp(self):
        self.admin = create_test_admin_user()
        self.client.force_login(self.admin)
        self.user = create_test_user()

    @classmethod
    def setUpTestData(cls):
        config = apps.get_app_config("authentik_tasks_schedules")
        config._on_startup_callback(None)

    def test_create(self):
        response = self.client.post(
            reverse("authentik_api:useroffboarding-list"),
            {
                "user": self.user.pk,
                "scheduled_for": (now() + timedelta(days=1)).isoformat(),
                "action": OffboardingAction.DELETE,
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], OffboardingStatus.PENDING)
        offboarding = UserOffboarding.objects.get(pk=response.data["id"])
        self.assertEqual(offboarding.created_by, self.admin)

    def test_create_in_past_rejected(self):
        response = self.client.post(
            reverse("authentik_api:useroffboarding-list"),
            {
                "user": self.user.pk,
                "scheduled_for": (now() - timedelta(days=1)).isoformat(),
                "action": OffboardingAction.DEACTIVATE,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("scheduled_for", response.data)

    def test_duplicate_pending_rejected(self):
        UserOffboarding.objects.create(
            user=self.user,
            scheduled_for=now() + timedelta(days=1),
            action=OffboardingAction.DEACTIVATE,
        )
        response = self.client.post(
            reverse("authentik_api:useroffboarding-list"),
            {
                "user": self.user.pk,
                "scheduled_for": (now() + timedelta(days=2)).isoformat(),
                "action": OffboardingAction.DEACTIVATE,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("user", response.data)

    def test_cancel(self):
        offboarding = UserOffboarding.objects.create(
            user=self.user,
            scheduled_for=now() + timedelta(days=1),
            action=OffboardingAction.DEACTIVATE,
        )
        response = self.client.delete(
            reverse("authentik_api:useroffboarding-detail", kwargs={"pk": offboarding.pk})
        )
        self.assertEqual(response.status_code, 204)
        self.assertFalse(UserOffboarding.objects.filter(pk=offboarding.pk).exists())
