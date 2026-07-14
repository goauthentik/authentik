import time
from datetime import timedelta
from threading import Event as ThreadEvent
from threading import Thread
from unittest.mock import patch

from django.apps import apps
from django.db import connection
from django.test import TransactionTestCase
from django.urls import reverse
from django.utils.timezone import now
from rest_framework.test import APITestCase

from authentik.core.models import (
    AuthenticatedSession,
    Session,
    Token,
    TokenIntents,
    User,
    UserTypes,
)
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.enterprise.lifecycle.api.offboarding import UserOffboardingSerializer
from authentik.enterprise.lifecycle.models import (
    OffboardingAction,
    OffboardingStatus,
    UserOffboarding,
)
from authentik.enterprise.lifecycle.offboarding import offboard_user
from authentik.enterprise.lifecycle.tasks import (
    MAX_OFFBOARDING_ATTEMPTS,
    execute_due_offboardings,
    execute_offboarding,
)
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

    def test_revoke_sessions_only(self):
        """Sessions and tokens toggle independently: sessions on, tokens off."""
        _add_session(self.user)
        _add_token(self.user)
        offboard_user(
            self.user,
            OffboardingAction.DEACTIVATE,
            revoke_sessions=True,
            revoke_tokens=False,
        )
        self.assertFalse(AuthenticatedSession.objects.filter(user=self.user).exists())
        self.assertTrue(Token.objects.filter(user=self.user).exists())

    def test_revoke_tokens_only(self):
        """Sessions and tokens toggle independently: tokens on, sessions off."""
        _add_session(self.user)
        _add_token(self.user)
        offboard_user(
            self.user,
            OffboardingAction.DEACTIVATE,
            revoke_sessions=False,
            revoke_tokens=True,
        )
        self.assertTrue(AuthenticatedSession.objects.filter(user=self.user).exists())
        self.assertFalse(Token.objects.filter(user=self.user).exists())


class TestOffboardingSweeper(APITestCase):
    @classmethod
    def setUpTestData(cls):
        config = apps.get_app_config("authentik_tasks_schedules")
        config._on_startup_callback(None)

    def setUp(self):
        self.user = create_test_user()

    def test_due_offboarding_dispatched_under_schedule(self):
        """The sweeper dispatches each due offboarding (and its schedule resolves)."""
        UserOffboarding.objects.create(
            user=self.user,
            scheduled_for=now() - timedelta(minutes=1),
            action=OffboardingAction.DEACTIVATE,
        )
        with patch(
            "authentik.enterprise.lifecycle.tasks.execute_offboarding.send_with_options"
        ) as send:
            execute_due_offboardings()
        send.assert_called_once()

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

    def test_failed_execution_is_atomic_and_retryable(self):
        """A mid-way failure rolls back every change and leaves the row retryable."""
        _add_session(self.user)
        _add_token(self.user)
        offboarding = UserOffboarding.objects.create(
            user=self.user,
            scheduled_for=now() - timedelta(minutes=1),
            action=OffboardingAction.DEACTIVATE,
        )
        # Sessions/tokens are revoked before the audit event is built; make the
        # event raise so the failure lands mid-offboarding.
        with patch(
            "authentik.enterprise.lifecycle.offboarding.Event.new",
            side_effect=RuntimeError("boom"),
        ):
            with self.assertRaises(RuntimeError):
                execute_offboarding(str(offboarding.pk))

        offboarding.refresh_from_db()
        self.user.refresh_from_db()
        # Nothing was applied: user still active, sessions/tokens intact.
        self.assertTrue(self.user.is_active)
        self.assertTrue(AuthenticatedSession.objects.filter(user=self.user).exists())
        self.assertTrue(Token.objects.filter(user=self.user).exists())
        # Still retryable, with the failed attempt recorded.
        self.assertEqual(offboarding.status, OffboardingStatus.PENDING)
        self.assertEqual(offboarding.attempts, 1)

    def test_offboarding_marked_failed_after_max_attempts(self):
        """A persistently failing offboarding goes terminal without touching the user."""
        offboarding = UserOffboarding.objects.create(
            user=self.user,
            scheduled_for=now() - timedelta(minutes=1),
            action=OffboardingAction.DEACTIVATE,
        )
        with patch(
            "authentik.enterprise.lifecycle.offboarding.Event.new",
            side_effect=RuntimeError("boom"),
        ):
            for _ in range(MAX_OFFBOARDING_ATTEMPTS):
                with self.assertRaises(RuntimeError):
                    execute_offboarding(str(offboarding.pk))

        offboarding.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(offboarding.status, OffboardingStatus.FAILED)
        self.assertEqual(offboarding.attempts, MAX_OFFBOARDING_ATTEMPTS)
        self.assertTrue(self.user.is_active)

    def test_redispatch_of_completed_offboarding_is_noop(self):
        """Re-dispatching an already-executed offboarding does not run it again."""
        offboarding = UserOffboarding.objects.create(
            user=self.user,
            scheduled_for=now() - timedelta(minutes=1),
            action=OffboardingAction.DEACTIVATE,
        )
        execute_offboarding(str(offboarding.pk))
        self.assertEqual(Event.objects.filter(action=EventAction.USER_OFFBOARDED).count(), 1)
        # The sweeper may re-queue the same row; the status guard must no-op.
        execute_offboarding(str(offboarding.pk))
        self.assertEqual(Event.objects.filter(action=EventAction.USER_OFFBOARDED).count(), 1)

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


class TestOffboardingConcurrency(TransactionTestCase):
    """Two workers must not offboard the same user twice."""

    def setUp(self):
        self.user = create_test_user()

    def test_concurrent_dispatch_executes_once(self):
        offboarding = UserOffboarding.objects.create(
            user=self.user,
            scheduled_for=now() - timedelta(minutes=1),
            action=OffboardingAction.DEACTIVATE,
        )
        pk = str(offboarding.pk)

        inside_lock = ThreadEvent()  # set once a worker holds the row lock
        may_finish = ThreadEvent()  # released once the other worker is running
        errors: list = []
        real_offboard = offboard_user

        def slow_offboard(*args, **kwargs):
            # The worker that reaches this holds the row lock; hold it briefly so
            # the other worker is forced to contend for the same PENDING row.
            inside_lock.set()
            may_finish.wait(timeout=10)
            return real_offboard(*args, **kwargs)

        class Worker(Thread):
            __test__ = False

            def run(self):
                try:
                    execute_offboarding(pk)
                except Exception as exc:  # noqa: BLE001
                    errors.append(exc)
                finally:
                    connection.close()

        with patch(
            "authentik.enterprise.lifecycle.offboarding.offboard_user", side_effect=slow_offboard
        ):
            first = Worker()
            first.start()
            self.assertTrue(inside_lock.wait(timeout=10), "worker never acquired the lock")
            # First worker now holds the lock inside slow_offboard. The second must
            # block on select_for_update; give it a moment to reach the lock, then
            # let the first finish. (The single-execution invariant holds for every
            # interleaving, since the first worker locks the row before the second starts.)
            second = Worker()
            second.start()
            time.sleep(0.5)
            may_finish.set()
            first.join(timeout=15)
            second.join(timeout=15)

        self.assertEqual(errors, [])
        self.assertEqual(Event.objects.filter(action=EventAction.USER_OFFBOARDED).count(), 1)
        offboarding.refresh_from_db()
        self.assertEqual(offboarding.status, OffboardingStatus.COMPLETED)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_cancel_racing_execution_does_not_clobber(self):
        """A cancel that loses the race to a running execution must not overwrite it."""
        offboarding = UserOffboarding.objects.create(
            user=self.user,
            scheduled_for=now() - timedelta(minutes=1),
            action=OffboardingAction.DEACTIVATE,
        )
        pk = str(offboarding.pk)

        inside_lock = ThreadEvent()  # set once the worker holds the row lock
        may_finish = ThreadEvent()  # released once the canceller is contending
        errors: list = []
        cancelled: list = []
        real_offboard = offboard_user

        def slow_offboard(*args, **kwargs):
            inside_lock.set()
            may_finish.wait(timeout=10)
            return real_offboard(*args, **kwargs)

        class Worker(Thread):
            __test__ = False

            def run(self):
                try:
                    execute_offboarding(pk)
                except Exception as exc:  # noqa: BLE001
                    errors.append(exc)
                finally:
                    connection.close()

        class Canceller(Thread):
            __test__ = False

            def run(self):
                try:
                    cancelled.append(UserOffboarding.objects.get(pk=pk).cancel())
                except Exception as exc:  # noqa: BLE001
                    errors.append(exc)
                finally:
                    connection.close()

        with patch(
            "authentik.enterprise.lifecycle.offboarding.offboard_user", side_effect=slow_offboard
        ):
            worker = Worker()
            worker.start()
            self.assertTrue(inside_lock.wait(timeout=10), "worker never acquired the lock")
            # Worker holds the lock mid-execution; the cancel must block on it,
            # then observe COMPLETED and refuse instead of clobbering the status.
            canceller = Canceller()
            canceller.start()
            time.sleep(0.5)
            may_finish.set()
            worker.join(timeout=15)
            canceller.join(timeout=15)

        self.assertEqual(errors, [])
        self.assertEqual(cancelled, [False])
        offboarding.refresh_from_db()
        self.assertEqual(offboarding.status, OffboardingStatus.COMPLETED)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)


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

    def test_duplicate_pending_race_returns_400(self):
        """If two requests race past validation, the DB constraint yields a 400, not a 500."""
        UserOffboarding.objects.create(
            user=self.user,
            scheduled_for=now() + timedelta(days=1),
            action=OffboardingAction.DEACTIVATE,
        )
        # Simulate the Time-of-Check to Time-of-Use: bypass the duplicate pre-check so the
        # insert is the first place the conflict is detected (the partial unique constraint).
        with patch.object(UserOffboardingSerializer, "validate", new=lambda self, attrs: attrs):
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
        # The losing insert did not create a second pending row.
        self.assertEqual(
            UserOffboarding.objects.filter(
                user=self.user, status=OffboardingStatus.PENDING
            ).count(),
            1,
        )

    def test_offboard_self_rejected(self):
        response = self.client.post(
            reverse("authentik_api:useroffboarding-list"),
            {
                "user": self.admin.pk,
                "scheduled_for": (now() + timedelta(days=1)).isoformat(),
                "action": OffboardingAction.DEACTIVATE,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("user", response.data)

    def test_offboard_internal_service_account_rejected(self):
        service_account = User.objects.create(
            username=generate_id(), type=UserTypes.INTERNAL_SERVICE_ACCOUNT
        )
        response = self.client.post(
            reverse("authentik_api:useroffboarding-list"),
            {
                "user": service_account.pk,
                "scheduled_for": (now() + timedelta(days=1)).isoformat(),
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
        # The row is retained as an audit record, transitioned to CANCELED.
        offboarding.refresh_from_db()
        self.assertEqual(offboarding.status, OffboardingStatus.CANCELED)
        self.assertIsNotNone(offboarding.executed_on)

    def test_cancel_frees_user_for_rescheduling(self):
        """A cancelled offboarding no longer blocks the unique-pending constraint."""
        offboarding = UserOffboarding.objects.create(
            user=self.user,
            scheduled_for=now() + timedelta(days=1),
            action=OffboardingAction.DEACTIVATE,
        )
        offboarding.cancel()
        response = self.client.post(
            reverse("authentik_api:useroffboarding-list"),
            {
                "user": self.user.pk,
                "scheduled_for": (now() + timedelta(days=2)).isoformat(),
                "action": OffboardingAction.DEACTIVATE,
            },
        )
        self.assertEqual(response.status_code, 201)

    def test_cancel_non_pending_rejected(self):
        offboarding = UserOffboarding.objects.create(
            user=self.user,
            scheduled_for=now() + timedelta(days=1),
            action=OffboardingAction.DEACTIVATE,
            status=OffboardingStatus.COMPLETED,
        )
        response = self.client.delete(
            reverse("authentik_api:useroffboarding-detail", kwargs={"pk": offboarding.pk})
        )
        self.assertEqual(response.status_code, 400)
        offboarding.refresh_from_db()
        self.assertEqual(offboarding.status, OffboardingStatus.COMPLETED)

    def test_update_not_allowed(self):
        """Records are immutable: PUT/PATCH must not rewrite an offboarding."""
        offboarding = UserOffboarding.objects.create(
            user=self.user,
            scheduled_for=now() + timedelta(days=1),
            action=OffboardingAction.DEACTIVATE,
        )
        url = reverse("authentik_api:useroffboarding-detail", kwargs={"pk": offboarding.pk})
        for method in (self.client.put, self.client.patch):
            response = method(url, {"action": OffboardingAction.DELETE})
            self.assertEqual(response.status_code, 405)
        offboarding.refresh_from_db()
        self.assertEqual(offboarding.action, OffboardingAction.DEACTIVATE)
