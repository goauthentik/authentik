from datetime import timedelta
from threading import Barrier, Thread
from unittest.mock import patch

from django.db import connection
from django.test import TransactionTestCase
from django.urls import reverse
from django.utils.timezone import now
from freezegun import freeze_time
from rest_framework.test import APITestCase

from authentik.core.models import Group, User, UserTypes
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.enterprise.lifecycle.expiration.models import UserExpirationRule
from authentik.enterprise.lifecycle.expiration.tasks import (
    apply_expiration_rule,
    apply_expiration_rules,
)
from authentik.enterprise.lifecycle.offboarding.models import (
    OffboardingAction,
    OffboardingStatus,
    UserOffboarding,
)
from authentik.enterprise.lifecycle.offboarding.tasks import execute_offboarding
from authentik.enterprise.tests import enterprise_test
from authentik.events.models import Event, EventAction
from authentik.lib.generators import generate_id
from authentik.policies.dummy.models import DummyPolicy
from authentik.policies.models import PolicyBinding

SEND_NOTIFICATION = (
    "authentik.enterprise.lifecycle.review.tasks.send_notification.send_with_options"
)
APPLY_RULE = (
    "authentik.enterprise.lifecycle.expiration.tasks.apply_expiration_rule.send_with_options"
)


def _backdate(user: User, *, last_login: timedelta | None, date_joined: timedelta):
    """Set the user's activity timestamps `n` ago (None leaves last_login null)."""
    User.objects.filter(pk=user.pk).update(
        last_login=None if last_login is None else now() - last_login,
        date_joined=now() - date_joined,
    )
    user.refresh_from_db()


def _dormant_user(days: int = 100, **kwargs) -> User:
    user = create_test_user(**kwargs)
    _backdate(user, last_login=timedelta(days=days), date_joined=timedelta(days=days + 1))
    return user


def _pending(user: User) -> UserOffboarding | None:
    return UserOffboarding.objects.filter(user=user, status=OffboardingStatus.PENDING).first()


class ExpirationTestCase(APITestCase):
    # No schedule reconciliation here: it would run every startup task synchronously
    # through the test broker (blueprint discovery included) inside the test
    # transaction. Saving a rule tolerates a missing schedule row, and the dispatch
    # itself is patched below.
    def setUp(self):
        # Rule saves dispatch an apply task; keep sweeps explicit in tests.
        patcher = patch(APPLY_RULE)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _rule(self, **kwargs) -> UserExpirationRule:
        kwargs.setdefault("name", generate_id())
        kwargs.setdefault("inactivity_duration", "days=90")
        return UserExpirationRule.objects.create(**kwargs)


class TestSelection(ExpirationTestCase):
    def test_all_users_by_last_login(self):
        rule = self._rule()
        dormant = _dormant_user(100)
        active = _dormant_user(10)
        self.assertEqual(rule.apply(), 1)
        pending = _pending(dormant)
        self.assertIsNotNone(pending)
        self.assertEqual(pending.rule, rule)
        self.assertEqual(pending.scheduled_at, dormant.last_login + timedelta(days=90))
        self.assertIsNone(pending.created_by)
        self.assertIsNone(_pending(active))

    def test_never_logged_in_counts_from_date_joined(self):
        rule = self._rule()
        never = create_test_user()
        _backdate(never, last_login=None, date_joined=timedelta(days=100))
        fresh = create_test_user()
        _backdate(fresh, last_login=None, date_joined=timedelta(days=10))
        rule.apply()
        self.assertEqual(_pending(never).scheduled_at, never.date_joined + timedelta(days=90))
        self.assertIsNone(_pending(fresh))

    def test_group_includes_descendants(self):
        parent = Group.objects.create(name=generate_id())
        child = Group.objects.create(name=generate_id())
        child.parents.add(parent)
        rule = self._rule(group=parent)
        in_child = _dormant_user()
        in_child.groups.add(child)
        outside = _dormant_user()
        rule.apply()
        self.assertIsNotNone(_pending(in_child))
        self.assertIsNone(_pending(outside))

    def test_user_types(self):
        rule = self._rule()
        service = _dormant_user(type=UserTypes.SERVICE_ACCOUNT)
        internal_service = _dormant_user(type=UserTypes.INTERNAL_SERVICE_ACCOUNT)
        rule.apply()
        self.assertIsNone(_pending(service))
        self.assertIsNone(_pending(internal_service))
        rule.user_types = [UserTypes.SERVICE_ACCOUNT, UserTypes.INTERNAL_SERVICE_ACCOUNT]
        rule.save()
        rule.apply()
        self.assertIsNotNone(_pending(service))
        # Always excluded, even when listed.
        self.assertIsNone(_pending(internal_service))

    def test_inactive_users_skipped(self):
        rule = self._rule()
        user = _dormant_user(is_active=False)
        rule.apply()
        self.assertIsNone(_pending(user))

    def test_superuser_exclusion_walks_descendants(self):
        su_group = Group.objects.create(name=generate_id(), is_superuser=True)
        child = Group.objects.create(name=generate_id())
        child.parents.add(su_group)
        grandparent = Group.objects.create(name=generate_id())
        su_group.parents.add(grandparent)
        in_child = _dormant_user()
        in_child.groups.add(child)
        in_grandparent = _dormant_user()
        in_grandparent.groups.add(grandparent)
        rule = self._rule()
        rule.apply()
        # Member of a child of a superuser group is a superuser; excluded.
        self.assertTrue(in_child.is_superuser)
        self.assertIsNone(_pending(in_child))
        # Member of a parent of a superuser group is not.
        self.assertFalse(in_grandparent.is_superuser)
        self.assertIsNotNone(_pending(in_grandparent))

    def test_superuser_included_when_not_excluded(self):
        su_group = Group.objects.create(name=generate_id(), is_superuser=True)
        user = _dormant_user()
        user.groups.add(su_group)
        self._rule(exclude_superusers=False).apply()
        self.assertIsNotNone(_pending(user))

    def test_warn_before_window(self):
        rule = self._rule(warn_before="days=7")
        in_window = _dormant_user(85)
        outside = _dormant_user(80)
        rule.apply()
        pending = _pending(in_window)
        self.assertIsNotNone(pending)
        self.assertGreater(pending.scheduled_at, now())
        self.assertIsNone(_pending(outside))
        event = Event.objects.get(action=EventAction.USER_EXPIRATION_WARNING)
        self.assertEqual(event.user["pk"], in_window.pk)
        self.assertEqual(event.context["rule"]["pk"], rule.pk.hex)

    def test_pending_manual_row_excluded(self):
        user = _dormant_user()
        manual = UserOffboarding.objects.create(user=user, scheduled_at=now() + timedelta(days=30))
        self._rule().apply()
        self.assertEqual(_pending(user), manual)

    def test_cancel_exempts_until_next_login(self):
        with freeze_time() as clock:
            group = Group.objects.create(name=generate_id())
            rule = self._rule(group=group)
            user = _dormant_user()
            user.groups.add(group)
            rule.apply()
            canceled = _pending(user)
            self.assertTrue(canceled.cancel())
            self.assertEqual(rule.apply(), 0)
            # Another inactivity period alone does not lift the exemption.
            clock.tick(timedelta(days=100))
            self.assertEqual(rule.apply(), 0)
            # A newer login lifts the exemption and restarts the inactivity clock.
            last_login = now()
            User.objects.filter(pk=user.pk).update(last_login=last_login)
            self.assertEqual(rule.apply(), 0)
            clock.tick(timedelta(days=89))
            self.assertEqual(rule.apply(), 0)
            clock.tick(timedelta(days=1))
            self.assertEqual(rule.apply(), 1)
            pending = _pending(user)
            self.assertIsNotNone(pending)
            self.assertNotEqual(pending.pk, canceled.pk)
            self.assertEqual(pending.scheduled_at, last_login + timedelta(days=90))
            canceled.refresh_from_db()
            self.assertEqual(canceled.status, OffboardingStatus.CANCELED)

    def test_reactivated_user_not_re_expired(self):
        rule = self._rule()
        user = _dormant_user()
        rule.apply()
        execute_offboarding(str(_pending(user).pk))
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        user.is_active = True
        user.save()
        self.assertEqual(rule.apply(), 0)
        self.assertIsNone(_pending(user))

    def test_failed_row_not_retried(self):
        rule = self._rule()
        user = _dormant_user()
        rule.apply()
        UserOffboarding.objects.filter(user=user).update(
            status=OffboardingStatus.FAILED, executed_at=now()
        )
        self.assertEqual(rule.apply(), 0)

    def test_sweep_is_idempotent(self):
        rule = self._rule()
        _dormant_user()
        self.assertEqual(rule.apply(), 1)
        self.assertEqual(rule.apply(), 0)
        self.assertEqual(
            Event.objects.filter(action=EventAction.USER_EXPIRATION_WARNING).count(), 1
        )

    def test_policy_bindings_filter_candidates(self):
        rule = self._rule()
        PolicyBinding.objects.create(
            target=rule,
            policy=DummyPolicy.objects.create(name=generate_id(), result=False),
            order=0,
        )
        user = _dormant_user()
        self.assertEqual(rule.apply(), 0)
        self.assertIsNone(_pending(user))

    def test_disabled_rule_does_nothing(self):
        rule = self._rule(enabled=False)
        _dormant_user()
        self.assertEqual(rule.apply(), 0)

    def test_rule_save_without_schedule_row_succeeds(self):
        from authentik.tasks.schedules.models import Schedule

        Schedule.objects.filter(actor_name=apply_expiration_rules.actor_name).delete()
        self._rule()

    def test_notifications_sent_per_transport(self):
        from authentik.events.models import NotificationTransport

        rule = self._rule()
        rule.notification_transports.add(NotificationTransport.objects.create(name=generate_id()))
        _dormant_user()
        with patch(SEND_NOTIFICATION) as send:
            rule.apply()
        send.assert_called_once()


class TestOverlapAndChange(ExpirationTestCase):
    def test_tighter_rule_takes_over_and_rewarns(self):
        loose = self._rule(inactivity_duration="days=180", warn_before="days=14")
        user = _dormant_user(170)
        loose.apply()
        first = _pending(user)
        self.assertEqual(first.rule, loose)
        tight = self._rule(inactivity_duration="days=90", action=OffboardingAction.DELETE)
        tight.apply()
        pending = _pending(user)
        self.assertEqual(pending.pk, first.pk)
        self.assertEqual(pending.rule, tight)
        self.assertEqual(pending.action, OffboardingAction.DELETE)
        self.assertEqual(pending.scheduled_at, user.last_login + timedelta(days=90))
        self.assertEqual(
            Event.objects.filter(action=EventAction.USER_EXPIRATION_WARNING).count(), 2
        )

    def test_looser_rule_does_not_touch_foreign_row(self):
        tight = self._rule(inactivity_duration="days=90")
        user = _dormant_user(100)
        tight.apply()
        first = _pending(user)
        loose = self._rule(inactivity_duration="days=95")
        loose.apply()
        pending = _pending(user)
        self.assertEqual(pending.rule, tight)
        self.assertEqual(pending.scheduled_at, first.scheduled_at)

    def test_loosened_duration_pushes_row_out_silently(self):
        rule = self._rule(inactivity_duration="days=90")
        user = _dormant_user(100)
        rule.apply()
        rule.inactivity_duration = "days=120"
        rule.save()
        rule.apply()
        pending = _pending(user)
        self.assertEqual(pending.scheduled_at, user.last_login + timedelta(days=120))
        self.assertEqual(
            Event.objects.filter(action=EventAction.USER_EXPIRATION_WARNING).count(), 1
        )

    def test_user_leaving_scope_deletes_row(self):
        group = Group.objects.create(name=generate_id())
        rule = self._rule(group=group)
        user = _dormant_user()
        user.groups.add(group)
        rule.apply()
        self.assertIsNotNone(_pending(user))
        user.groups.remove(group)
        rule.apply()
        self.assertIsNone(_pending(user))
        self.assertFalse(UserOffboarding.objects.filter(user=user).exists())


class TestConcurrency(TransactionTestCase):
    """Two rules sweeping the same user at once converge on one row owned by the tighter rule."""

    def test_concurrent_sweeps_converge_on_tighter_rule(self):
        with patch(APPLY_RULE):
            loose = UserExpirationRule.objects.create(
                name=generate_id(), inactivity_duration="days=95"
            )
            tight = UserExpirationRule.objects.create(
                name=generate_id(), inactivity_duration="days=90"
            )
        user = _dormant_user(100)
        barrier = Barrier(2, timeout=10)
        errors: list = []

        def sweep(rule: UserExpirationRule):
            try:
                # Bound database waits so cleanup can join workers after a timeout.
                with connection.cursor() as cursor:
                    cursor.execute("SET statement_timeout = '10s'")
                barrier.wait()
                rule.apply()
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)
            finally:
                connection.close()

        # Both rules see the user as a candidate regardless of what the other rule
        # inserted, so the insert race and the IntegrityError path are exercised.
        with patch.object(
            UserExpirationRule, "candidates", lambda self: User.objects.filter(pk=user.pk)
        ):
            threads = [Thread(target=sweep, args=(rule,)) for rule in (loose, tight)]
            started_threads = []
            try:
                for thread in threads:
                    thread.start()
                    started_threads.append(thread)
                for thread in started_threads:
                    thread.join(timeout=15)
                self.assertFalse(
                    any(thread.is_alive() for thread in started_threads),
                    "Expiration sweep workers did not finish before the timeout",
                )
            finally:
                barrier.abort()
                # Keep the patch and database intact until every worker has exited.
                for thread in started_threads:
                    thread.join()

        self.assertEqual(errors, [])
        self.assertEqual(UserOffboarding.objects.filter(user=user).count(), 1)
        # Whichever rule won the insert, the next sweep converges on the tighter one.
        apply_expiration_rule(str(loose.pk))
        apply_expiration_rule(str(tight.pk))
        self.assertEqual(UserOffboarding.objects.filter(user=user).count(), 1)
        pending = _pending(user)
        self.assertEqual(pending.rule, tight)
        self.assertEqual(pending.scheduled_at, user.last_login + timedelta(days=90))


class TestWithdrawal(ExpirationTestCase):
    def test_login_withdraws_row(self):
        rule = self._rule()
        user = _dormant_user()
        rule.apply()
        self.assertIsNotNone(_pending(user))
        self.client.force_login(user)
        self.assertFalse(UserOffboarding.objects.filter(user=user).exists())

    def test_last_login_write_without_login_withdraws_row(self):
        rule = self._rule()
        user = _dormant_user()
        rule.apply()
        user.last_login = now()
        user.save(update_fields=["last_login"])
        self.assertFalse(UserOffboarding.objects.filter(user=user).exists())

    def test_full_save_with_new_last_login_withdraws_row(self):
        rule = self._rule()
        user = _dormant_user()
        rule.apply()
        user.last_login = now()
        user.save()
        self.assertFalse(UserOffboarding.objects.filter(user=user).exists())

    def test_unrelated_save_keeps_row(self):
        rule = self._rule()
        user = _dormant_user()
        rule.apply()
        user.name = generate_id()
        user.save()
        self.assertIsNotNone(_pending(user))

    def test_manual_row_not_withdrawn_by_login(self):
        user = _dormant_user()
        UserOffboarding.objects.create(user=user, scheduled_at=now() + timedelta(days=1))
        self.client.force_login(user)
        self.assertIsNotNone(_pending(user))


class TestExecution(ExpirationTestCase):
    def test_generated_row_executes_with_rule_context(self):
        rule = self._rule()
        user = _dormant_user()
        rule.apply()
        execute_offboarding(str(_pending(user).pk))
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        event = Event.objects.get(action=EventAction.USER_OFFBOARDED)
        self.assertEqual(event.context["rule"]["pk"], rule.pk.hex)

    def test_recheck_disabled_rule(self):
        rule = self._rule()
        user = _dormant_user()
        rule.apply()
        row = _pending(user)
        rule.enabled = False
        rule.save()
        execute_offboarding(str(row.pk))
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertFalse(UserOffboarding.objects.filter(pk=row.pk).exists())

    def test_recheck_user_left_group(self):
        group = Group.objects.create(name=generate_id())
        rule = self._rule(group=group)
        user = _dormant_user()
        user.groups.add(group)
        rule.apply()
        row = _pending(user)
        user.groups.remove(group)
        execute_offboarding(str(row.pk))
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertFalse(UserOffboarding.objects.filter(pk=row.pk).exists())

    def test_recheck_login_that_bypassed_hooks(self):
        rule = self._rule()
        user = _dormant_user()
        rule.apply()
        row = _pending(user)
        User.objects.filter(pk=user.pk).update(last_login=now())
        execute_offboarding(str(row.pk))
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertFalse(UserOffboarding.objects.filter(pk=row.pk).exists())

    def test_rule_delete_removes_pending_keeps_history(self):
        rule = self._rule()
        done = _dormant_user()
        rule.apply()
        done_row = _pending(done)
        execute_offboarding(str(done_row.pk))
        pending_user = _dormant_user()
        rule.apply()
        pending_row = _pending(pending_user)
        rule.delete()
        self.assertFalse(UserOffboarding.objects.filter(pk=pending_row.pk).exists())
        done_row.refresh_from_db()
        self.assertEqual(done_row.status, OffboardingStatus.COMPLETED)
        self.assertIsNone(done_row.rule)

    def test_sweeper_dispatches_enabled_rules(self):
        self._rule()
        self._rule(enabled=False)
        with patch(APPLY_RULE) as send:
            apply_expiration_rules.send()
        send.assert_called_once()

    def test_without_license_sweeper_and_generated_rows_stop(self):
        rule = self._rule()
        user = _dormant_user()
        rule.apply()
        row = _pending(user)
        manual_user = create_test_user()
        manual = UserOffboarding.objects.create(
            user=manual_user, scheduled_at=now() - timedelta(minutes=1)
        )
        with patch(
            "authentik.enterprise.apps.AuthentikEnterpriseConfig.enabled", return_value=False
        ):
            with patch(APPLY_RULE) as send:
                apply_expiration_rules.send()
            send.assert_not_called()
            execute_offboarding(str(row.pk))
            execute_offboarding(str(manual.pk))
        row.refresh_from_db()
        self.assertEqual(row.status, OffboardingStatus.PENDING)
        manual.refresh_from_db()
        self.assertEqual(manual.status, OffboardingStatus.COMPLETED)


@enterprise_test()
class TestAPI(ExpirationTestCase):
    def setUp(self):
        super().setUp()
        self.admin = create_test_admin_user()
        self.client.force_login(self.admin)

    def test_create(self):
        response = self.client.post(
            reverse("authentik_api:userexpirationrule-list"),
            {"name": generate_id(), "inactivity_duration": "days=30", "warn_before": "days=7"},
        )
        self.assertEqual(response.status_code, 201, response.content)
        rule = UserExpirationRule.objects.get(pk=response.data["pk"])
        self.assertEqual(rule.user_types, [UserTypes.INTERNAL, UserTypes.EXTERNAL])

    def test_warn_before_must_be_shorter(self):
        response = self.client.post(
            reverse("authentik_api:userexpirationrule-list"),
            {"name": generate_id(), "inactivity_duration": "days=7", "warn_before": "days=7"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("warn_before", response.data)

    def test_invalid_duration(self):
        response = self.client.post(
            reverse("authentik_api:userexpirationrule-list"),
            {"name": generate_id(), "inactivity_duration": "soon"},
        )
        self.assertEqual(response.status_code, 400)

    def test_internal_service_account_type_rejected(self):
        response = self.client.post(
            reverse("authentik_api:userexpirationrule-list"),
            {"name": generate_id(), "user_types": [UserTypes.INTERNAL_SERVICE_ACCOUNT]},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("user_types", response.data)

    def test_preview(self):
        rule = self._rule()
        user = _dormant_user()
        _dormant_user(10)
        response = self.client.get(
            reverse("authentik_api:userexpirationrule-preview", kwargs={"pk": rule.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["users"][0]["username"], user.username)
        self.assertEqual(rule.apply(), 1)

    def test_offboarding_exposes_rule(self):
        rule = self._rule()
        _dormant_user()
        rule.apply()
        response = self.client.get(
            reverse("authentik_api:useroffboarding-list"), {"rule__isnull": "false"}
        )
        self.assertEqual(response.data["pagination"]["count"], 1)
        self.assertEqual(response.data["results"][0]["rule_obj"]["name"], rule.name)
        response = self.client.get(
            reverse("authentik_api:useroffboarding-list"), {"rule__isnull": "true"}
        )
        self.assertEqual(response.data["pagination"]["count"], 0)

    def test_rule_rejected_on_offboarding_create(self):
        rule = self._rule()
        user = create_test_user()
        response = self.client.post(
            reverse("authentik_api:useroffboarding-list"),
            {
                "user": user.pk,
                "scheduled_at": (now() + timedelta(days=1)).isoformat(),
                "rule": str(rule.pk),
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertIsNone(UserOffboarding.objects.get(pk=response.data["id"]).rule)


class TestAPIWithoutLicense(ExpirationTestCase):
    def test_create_refused(self):
        self.client.force_login(create_test_admin_user())
        with patch("authentik.enterprise.license.LicenseKey.cached_summary") as summary:
            summary.return_value.status.is_valid = False
            response = self.client.post(
                reverse("authentik_api:userexpirationrule-list"), {"name": generate_id()}
            )
        self.assertEqual(response.status_code, 400)
