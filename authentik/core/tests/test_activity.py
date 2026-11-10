"""Activity recording, attribution, and historical backfill."""

from datetime import timedelta
from importlib import import_module
from unittest.mock import patch

from django.db import connection
from django.test import TestCase, TransactionTestCase
from django.utils.timezone import now
from freezegun import freeze_time

from authentik.core.models import USER_ACTIVITY_INTERVAL, UserActivity
from authentik.core.tests.utils import create_test_user
from authentik.events.models import Event, EventAction
from authentik.events.signals import event_post_save_activity


class TestUserActivity(TestCase):
    def test_monotonic_throttle_boundaries_and_invalid_ids(self):
        user = create_test_user()
        at = now()
        UserActivity.objects.record(user.pk, at)
        for delta in (-timedelta(days=1), USER_ACTIVITY_INTERVAL - timedelta(microseconds=1)):
            UserActivity.objects.record(user.pk, at + delta)
            self.assertEqual(UserActivity.objects.get(user=user).last_activity_at, at)
        UserActivity.objects.record(user.pk, at + USER_ACTIVITY_INTERVAL)
        self.assertEqual(
            UserActivity.objects.get(user=user).last_activity_at, at + USER_ACTIVITY_INTERVAL
        )
        user.delete()
        for invalid in (None, "1", True, 10**100):
            UserActivity.objects.record(invalid, at)
        self.assertFalse(UserActivity.objects.exists())

    def test_late_activity_for_deleted_user_is_allowed(self):
        user = create_test_user()
        user_id = user.pk
        UserActivity.objects.record(user_id)
        user.delete()
        self.assertFalse(UserActivity.objects.filter(user_id=user_id).exists())
        UserActivity.objects.record(user_id)
        self.assertTrue(UserActivity.objects.filter(user_id=user_id).exists())

    def test_event_attribution_and_resaves(self):
        admin, target = create_test_user(), create_test_user()
        at = now()
        with freeze_time(at):
            event = Event.new(EventAction.LOGIN)
            event.user = {"pk": admin.pk, "on_behalf_of": {"pk": target.pk}}
            event.save()
        self.assertFalse(UserActivity.objects.filter(user=target).exists())
        with freeze_time(at + timedelta(days=1)):
            event.save()
            event_post_save_activity(Event, event, created=True, raw=True)
        self.assertEqual(UserActivity.objects.get(user=admin).last_activity_at, at)

    def test_backfill_matches_attribution_and_preserves_newer_activity(self):
        users = [create_test_user() for _ in range(3)]
        at = now() - timedelta(days=2)
        with patch("authentik.events.signals.UserActivity.objects.record"):
            for index, action in enumerate(
                (EventAction.LOGIN, EventAction.AUTHORIZE_APPLICATION, EventAction.LOGIN_FAILED)
            ):
                with freeze_time(at):
                    Event.new(action).set_user(users[index]).save()
            event = Event.new(EventAction.LOGIN)
            event.user = {"pk": "invalid", "on_behalf_of": {"pk": users[2].pk}}
            event.save()
        UserActivity.objects.record(users[0].pk)
        current = UserActivity.objects.get(user=users[0]).last_activity_at
        migration = import_module("authentik.core.migrations.0070_backfill_useractivity")
        with connection.cursor() as cursor:
            cursor.execute(migration.Migration.operations[0].sql)
        self.assertEqual(UserActivity.objects.get(user=users[0]).last_activity_at, current)
        self.assertEqual(UserActivity.objects.get(user=users[1]).last_activity_at, at)
        self.assertFalse(UserActivity.objects.filter(user=users[2]).exists())


class TestConcurrentActivityRecording(TransactionTestCase):
    def test_concurrent_first_writes_keep_the_newest_timestamp(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier

        from django.db import close_old_connections

        user = create_test_user()
        at = now()
        barrier = Barrier(2)

        def record(timestamp):
            close_old_connections()
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SET statement_timeout = '10s'")
                barrier.wait(timeout=5)
                UserActivity.objects.record(user.pk, timestamp)
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [
                pool.submit(record, timestamp) for timestamp in (at, at + USER_ACTIVITY_INTERVAL)
            ]
            try:
                for future in futures:
                    future.result(timeout=15)
            finally:
                barrier.abort()
        self.assertEqual(
            UserActivity.objects.get(user=user).last_activity_at, at + USER_ACTIVITY_INTERVAL
        )
