"""Event activity clocks, reconciliation, exemptions, and deadline boundaries."""

from datetime import timedelta
from unittest.mock import patch

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils.timezone import now
from freezegun import freeze_time

from authentik.core.models import Group, User
from authentik.enterprise.lifecycle.expiration.api import UserExpirationRuleSerializer
from authentik.enterprise.lifecycle.expiration.models import ActivityBasis, UserExpirationRule
from authentik.enterprise.lifecycle.expiration.tests.test_expiration import (
    ExpirationTestCase,
    _dormant_user,
    _pending,
)
from authentik.enterprise.lifecycle.offboarding.models import (
    OffboardingAction,
    UserOffboarding,
)
from authentik.enterprise.lifecycle.offboarding.tasks import execute_offboarding
from authentik.events.activity import REFRESH_ACTIVITY_INTERVAL, load_activity, with_activity
from authentik.events.models import Event, EventAction
from authentik.lib.generators import generate_id
from authentik.policies.dummy.models import DummyPolicy
from authentik.policies.models import PolicyBinding


class TestActivity(ExpirationTestCase):
    def _event(self, user, action, *, created=None):
        event = Event.new(action).set_user(user)
        event.save()
        if created is not None:
            Event.objects.filter(pk=event.pk).update(created=created)
        return event

    def test_defaults_and_serializer(self):
        rule = UserExpirationRule.objects.create(name=generate_id())
        self.assertFalse(rule.enabled)
        self.assertEqual(rule.activity_basis, ActivityBasis.SUCCESSFUL_EVENTS)
        self.assertEqual(
            UserExpirationRuleSerializer(rule).data["activity_basis"], "successful_events"
        )

    def test_recent_success_only_protects_event_mode(self):
        for action in (
            EventAction.LOGIN,
            EventAction.AUTHORIZE_APPLICATION,
            EventAction.TOKEN_REFRESH,
        ):
            with self.subTest(action=action):
                user = _dormant_user()
                self._event(user, action)
                event_rule = self._rule()
                login_rule = self._rule(activity_basis=ActivityBasis.LAST_LOGIN)
                self.assertFalse(event_rule.candidates().filter(pk=user.pk).exists())
                self.assertTrue(login_rule.candidates().filter(pk=user.pk).exists())

    def test_failure_warning_and_target_references_do_not_count(self):
        user = _dormant_user()
        for action in (
            EventAction.LOGIN_FAILED,
            EventAction.SUSPICIOUS_REQUEST,
            EventAction.USER_EXPIRATION_WARNING,
            EventAction.POLICY_EXECUTION,
            EventAction.MODEL_UPDATED,
        ):
            self._event(user, action)
        event = Event.new(EventAction.LOGIN, target=user)
        event.user = {"pk": user.pk + 1, "on_behalf_of": {"pk": user.pk}}
        event.save()
        Event.new(EventAction.AUTHORIZE_APPLICATION).save()
        self.assertTrue(self._rule().candidates().filter(pk=user.pk).exists())

    def test_exact_events_have_no_refresh_allowance(self):
        user = _dormant_user()
        at = now() - timedelta(hours=2)
        self._event(user, EventAction.AUTHORIZE_APPLICATION, created=at)
        rule = self._rule(inactivity_duration="hours=1")
        self.assertEqual(rule.due_at(user), at + timedelta(hours=1))
        self.assertTrue(rule.candidates().filter(pk=user.pk).exists())

    def test_latest_evidence_wins_including_missing_login(self):
        user = _dormant_user()
        User.objects.filter(pk=user.pk).update(last_login=None)
        user.refresh_from_db()
        at = now() - timedelta(hours=2)
        self._event(user, EventAction.TOKEN_REFRESH, created=at - timedelta(days=2))
        self._event(user, EventAction.LOGIN, created=at)
        self.assertEqual(self._rule().due_at(user), at + timedelta(days=90))

    def test_refresh_boundary_preview_sweep_and_execution(self):
        for offset in (-1, 0, 1):
            with self.subTest(offset=offset), freeze_time() as clock:
                group = Group.objects.create(name=generate_id())
                rule = self._rule(group=group, inactivity_duration="minutes=30")
                user = _dormant_user()
                user.groups.add(group)
                at = now()
                self._event(user, EventAction.TOKEN_REFRESH)
                due = at + REFRESH_ACTIVITY_INTERVAL + timedelta(minutes=30)
                clock.move_to(due + timedelta(microseconds=offset))
                self.assertEqual(rule.due_at(user), due)
                self.assertEqual(rule.candidates().filter(pk=user.pk).exists(), offset >= 0)
                self.assertEqual(rule.apply(), int(offset >= 0))
                if offset >= 0:
                    execute_offboarding(str(_pending(user).pk))
                    user.refresh_from_db()
                    self.assertFalse(user.is_active)

    def test_warning_row_does_not_execute_before_refresh_deadline(self):
        with freeze_time() as clock:
            group = Group.objects.create(name=generate_id())
            user = _dormant_user()
            user.groups.add(group)
            self._event(user, EventAction.TOKEN_REFRESH)
            rule = self._rule(group=group, inactivity_duration="hours=1", warn_before="minutes=30")
            due = now() + REFRESH_ACTIVITY_INTERVAL + timedelta(hours=1)
            clock.move_to(due - timedelta(minutes=30))
            self.assertEqual(rule.apply(), 1)
            row = _pending(user)
            clock.move_to(due - timedelta(microseconds=1))
            execute_offboarding(str(row.pk))
            user.refresh_from_db()
            self.assertTrue(user.is_active)
            row.refresh_from_db()
            self.assertEqual(row.scheduled_at, due)
            clock.move_to(due)
            execute_offboarding(str(row.pk))
            user.refresh_from_db()
            self.assertFalse(user.is_active)

    def test_new_event_withdraws_on_reconcile_and_execution(self):
        for sweep in (False, True):
            with self.subTest(sweep=sweep), freeze_time() as clock:
                user = _dormant_user()
                rule = self._rule()
                rule.apply()
                row = _pending(user)
                clock.tick(timedelta(seconds=1))
                self._event(user, EventAction.AUTHORIZE_APPLICATION)
                # No Event save hook: the row remains visible until reconciliation.
                self.assertTrue(UserOffboarding.objects.filter(pk=row.pk).exists())
                if sweep:
                    rule.apply()
                else:
                    execute_offboarding(str(row.pk))
                self.assertFalse(UserOffboarding.objects.filter(pk=row.pk).exists())
                user.refresh_from_db()
                self.assertTrue(user.is_active)

    def test_failures_and_historical_events_do_not_withdraw(self):
        user = _dormant_user()
        rule = self._rule()
        rule.apply()
        row = _pending(user)
        self._event(user, EventAction.SUSPICIOUS_REQUEST)
        self._event(user, EventAction.LOGIN_FAILED)
        self._event(user, EventAction.LOGIN, created=row.created_at - timedelta(days=100))
        rule._revisit_owned_rows()
        self.assertEqual(_pending(user).pk, row.pk)

    def test_events_do_not_withdraw_manual_or_login_only_rows(self):
        for manual in (False, True):
            with self.subTest(manual=manual):
                user = _dormant_user()
                rule = self._rule(activity_basis=ActivityBasis.LAST_LOGIN)
                if manual:
                    row = UserOffboarding.objects.create(user=user, scheduled_at=now())
                else:
                    rule.apply()
                    row = _pending(user)
                self._event(user, EventAction.TOKEN_REFRESH)
                rule._revisit_owned_rows()
                self.assertEqual(_pending(user).pk, row.pk)

    def test_basis_edit_updates_queued_execution(self):
        with freeze_time() as clock:
            user = _dormant_user()
            rule = self._rule(activity_basis=ActivityBasis.LAST_LOGIN)
            rule.apply()
            row = _pending(user)
            clock.tick(timedelta(seconds=1))
            self._event(user, EventAction.TOKEN_REFRESH)
            rule.activity_basis = ActivityBasis.SUCCESSFUL_EVENTS
            rule.save()
            execute_offboarding(str(row.pk))
            self.assertIsNone(_pending(user))
            user.refresh_from_db()
            self.assertTrue(user.is_active)

    @freeze_time()
    def test_mixed_bases_rank_by_actual_due_date(self):
        user = _dormant_user()
        self._event(user, EventAction.AUTHORIZE_APPLICATION, created=now() - timedelta(days=80))
        event_rule = self._rule(inactivity_duration="days=70", action=OffboardingAction.DELETE)
        login_rule = self._rule(
            inactivity_duration="days=90", activity_basis=ActivityBasis.LAST_LOGIN
        )
        # Both expired ten days ago, even though the durations differ.
        self.assertEqual(event_rule.due_at(user), login_rule.due_at(user))
        event_rule.apply()
        execute_offboarding(str(_pending(user).pk))
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        self.assertEqual(user.offboardings.get().rule, login_rule)

    def test_cancel_exemption_survives_activity_and_event_pruning(self):
        with freeze_time() as clock:
            user = _dormant_user()
            rule = self._rule()
            rule.apply()
            _pending(user).cancel()
            clock.tick(timedelta(seconds=1))
            event = self._event(user, EventAction.AUTHORIZE_APPLICATION)
            clock.tick(timedelta(days=100))
            self.assertFalse(rule.candidates().filter(pk=user.pk).exists())
            event.delete()
            self.assertFalse(rule.candidates().filter(pk=user.pk).exists())
            User.objects.filter(pk=user.pk).update(last_login=now() - timedelta(days=91))
            self.assertTrue(rule.candidates().filter(pk=user.pk).exists())

    def test_active_users_are_removed_before_dynamic_policies(self):
        user = _dormant_user()
        self._event(user, EventAction.LOGIN)
        rule = self._rule()
        policy = DummyPolicy.objects.create(name=generate_id(), result=True)
        PolicyBinding.objects.create(target=rule, policy=policy, order=0)
        with patch.object(
            DummyPolicy, "passes", side_effect=AssertionError("active user evaluated")
        ):
            self.assertFalse(rule.candidates().filter(pk=user.pk).exists())

    def test_candidate_queries_do_not_grow_with_users(self):
        group = Group.objects.create(name=generate_id())
        rule = self._rule(group=group)
        user = _dormant_user()
        user.groups.add(group)
        with CaptureQueriesContext(connection) as one:
            users = list(rule.candidates())
            for candidate in users:
                rule.due_at(candidate)
        for _ in range(10):
            another = _dormant_user()
            another.groups.add(group)
            self._event(another, EventAction.LOGIN_FAILED)
        with CaptureQueriesContext(connection) as many:
            users = list(rule.candidates())
            for candidate in users:
                rule.due_at(candidate)
        self.assertEqual(len(users), 11)
        self.assertEqual(len(one), len(many))

    def test_pending_row_inserted_after_activity_load_is_skipped(self):
        first = _dormant_user()
        second = _dormant_user()
        owner = self._rule(
            inactivity_duration="days=120",
            warn_before="days=30",
            activity_basis=ActivityBasis.LAST_LOGIN,
        )
        rule = self._rule(activity_basis=ActivityBasis.LAST_LOGIN)
        UserOffboarding.objects.create(user=first, rule=owner, scheduled_at=owner.due_at(first))

        def load_then_insert(queryset):
            users = list(with_activity(queryset))
            # Another sweep commits this row between the activity batch and the
            # takeover query. It was not part of the users already evaluated.
            UserOffboarding.objects.create(
                user=second, rule=owner, scheduled_at=owner.due_at(second)
            )
            return users

        with patch(
            "authentik.enterprise.lifecycle.expiration.models.with_activity",
            side_effect=load_then_insert,
        ):
            rule._tighten_foreign_rows()
        self.assertEqual(_pending(first).rule, rule)
        self.assertEqual(_pending(second).rule, owner)

    def test_preloaded_activity_reused_for_competing_rules(self):
        user = _dormant_user()
        rules = [self._rule(), self._rule(activity_basis=ActivityBasis.LAST_LOGIN)]
        load_activity(user)
        with self.assertNumQueries(0):
            for rule in rules:
                rule.rank(user)

    def test_refresh_evidence_survives_until_due_with_required_retention(self):
        with freeze_time() as clock:
            user = _dormant_user()
            rule = self._rule(inactivity_duration="hours=1")
            event = self._event(user, EventAction.TOKEN_REFRESH)
            due = now() + REFRESH_ACTIVITY_INTERVAL + timedelta(hours=1)
            Event.objects.filter(pk=event.pk).update(expires=due)
            clock.move_to(due - timedelta(microseconds=1))
            Event.objects.filter(expires__lt=now()).delete()
            self.assertTrue(Event.objects.filter(pk=event.pk).exists())
            self.assertFalse(rule.candidates().filter(pk=user.pk).exists())
            clock.move_to(due)
            self.assertTrue(rule.candidates().filter(pk=user.pk).exists())
            clock.tick(timedelta(microseconds=1))
            Event.objects.filter(expires__lt=now()).delete()
            self.assertFalse(Event.objects.filter(pk=event.pk).exists())
            self.assertTrue(rule.candidates().filter(pk=user.pk).exists())

    @freeze_time()
    def test_longer_login_duration_can_win_over_shorter_event_duration(self):
        user = _dormant_user()
        self._event(user, EventAction.AUTHORIZE_APPLICATION, created=now() - timedelta(days=80))
        event_rule = self._rule(inactivity_duration="days=75", action=OffboardingAction.DELETE)
        login_rule = self._rule(
            inactivity_duration="days=90", activity_basis=ActivityBasis.LAST_LOGIN
        )
        self.assertLess(login_rule.due_at(user), event_rule.due_at(user))
        event_rule.apply()
        execute_offboarding(str(_pending(user).pk))
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        self.assertEqual(user.offboardings.get().rule, login_rule)
