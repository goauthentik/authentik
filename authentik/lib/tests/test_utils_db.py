"""PostgreSQL regression tests for bounded deletion."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Event

from django.db import connection, connections, transaction
from django.db.models.signals import pre_delete
from django.test import TransactionTestCase
from django.test.utils import CaptureQueriesContext
from django.utils.timezone import now
from django_channels_postgres.models import GroupChannel, Message
from django_postgres_cache.models import CacheEntry
from django_postgres_cache.tasks import clear_expired_cache

from authentik.lib.utils.db import delete_in_batches


class TestDeleteInBatches(TransactionTestCase):
    """Use committed rows and separate connections to exercise actual row locks."""

    def setUp(self):
        self.cutoff = now()
        self.expired_at = self.cutoff - timedelta(hours=1)
        self.future = self.cutoff + timedelta(hours=1)
        CacheEntry.objects.all().delete()

    def create_entries(self, count: int) -> None:
        CacheEntry.objects.bulk_create(
            [
                CacheEntry(
                    cache_key=f"batch-test-{index:04}", value="value", expires=self.expired_at
                )
                for index in range(count)
            ]
        )

    def expired(self):
        return CacheEntry.objects.filter(expires__lt=self.cutoff)

    def test_empty(self):
        self.assertEqual(delete_in_batches(self.expired()), 0)

    def test_invalid_batch_size(self):
        for batch_size in (0, -1):
            with self.subTest(batch_size=batch_size), self.assertRaises(ValueError):
                delete_in_batches(self.expired(), batch_size=batch_size)

    def test_multiple_batches_preserve_unexpired(self):
        self.create_entries(5)
        CacheEntry.objects.create(cache_key="future", value="value", expires=self.future)
        CacheEntry.objects.create(cache_key="boundary", value="value", expires=self.cutoff)
        self.assertEqual(delete_in_batches(self.expired(), batch_size=2), 5)
        self.assertSetEqual(
            set(CacheEntry.objects.values_list("pk", flat=True)), {"future", "boundary"}
        )

    def test_query_count_scales_with_batches(self):
        self.create_entries(25)
        with CaptureQueriesContext(connection) as queries:
            self.assertEqual(delete_in_batches(self.expired(), batch_size=10), 25)
        deletes = [query for query in queries if query["sql"].startswith("DELETE")]
        self.assertEqual(len(deletes), 3)
        # Three batches plus an empty probe, including BEGIN/COMMIT per batch.
        self.assertLessEqual(len(queries), 18)

    def test_cache_cleanup_integration(self):
        self.create_entries(1001)
        CacheEntry.objects.create(cache_key="future", value="value", expires=self.future)
        self.assertEqual(clear_expired_cache(), 1001)
        self.assertEqual(list(CacheEntry.objects.values_list("pk", flat=True)), ["future"])

    def test_channel_models(self):
        for model, fields in (
            (Message, {"channel": "batch-test", "message": b"message"}),
            (GroupChannel, {"channel": "batch-test", "group_key": "batch-test"}),
        ):
            with self.subTest(model=model):
                model.objects.bulk_create(
                    [model(expires=self.expired_at, **fields) for _ in range(5)]
                )
                retained = model.objects.create(expires=self.future, **fields)
                self.assertEqual(
                    delete_in_batches(
                        model.objects.filter(channel="batch-test", expires__lt=self.cutoff),
                        batch_size=2,
                    ),
                    5,
                )
                self.assertTrue(model.objects.filter(pk=retained.pk).exists())

    def test_locked_entry_is_skipped_then_cleaned(self):
        self.create_entries(3)
        with ThreadPoolExecutor(max_workers=1) as executor:
            with transaction.atomic():
                CacheEntry.objects.select_for_update().get(pk="batch-test-0000")
                deleted = executor.submit(self.delete_on_other_connection).result(timeout=10)
                self.assertEqual(deleted, 2)
                self.assertTrue(CacheEntry.objects.filter(pk="batch-test-0000").exists())
        self.assertEqual(delete_in_batches(self.expired()), 1)

    def test_concurrent_refresh_survives(self):
        self.create_entries(2)
        with ThreadPoolExecutor(max_workers=1) as executor:
            with transaction.atomic():
                CacheEntry.objects.filter(pk="batch-test-0000").update(expires=self.future)
                deleted = executor.submit(self.delete_on_other_connection).result(timeout=10)
                self.assertEqual(deleted, 1)
        self.assertEqual(delete_in_batches(self.expired()), 0)
        self.assertEqual(CacheEntry.objects.get(pk="batch-test-0000").expires, self.future)

    def test_concurrent_cleanups_do_not_double_count(self):
        self.create_entries(4)
        selected = Event()
        release = Event()

        def pause_first_batch(sender, instance, **kwargs):
            if instance.pk == "batch-test-0000":
                selected.set()
                if not release.wait(timeout=10):
                    raise TimeoutError("Cleanup test did not release the first batch")

        # Exercise Django's collector path as well as its fast-delete path.
        pre_delete.connect(pause_first_batch, sender=CacheEntry)
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                first = executor.submit(self.delete_on_other_connection)
                try:
                    self.assertTrue(selected.wait(timeout=10))
                    second_count = delete_in_batches(self.expired(), batch_size=2)
                finally:
                    release.set()
                self.assertEqual(first.result(timeout=10), 2)
                self.assertEqual(second_count, 2)
        finally:
            pre_delete.disconnect(pause_first_batch, sender=CacheEntry)
        self.assertFalse(self.expired().exists())

    def test_completed_batch_survives_later_failure(self):
        self.create_entries(4)

        def fail_second_batch(sender, instance, **kwargs):
            if instance.pk == "batch-test-0002":
                raise RuntimeError("Second batch failed")

        pre_delete.connect(fail_second_batch, sender=CacheEntry)
        try:
            with self.assertRaisesMessage(RuntimeError, "Second batch failed"):
                delete_in_batches(self.expired(), batch_size=2)
        finally:
            pre_delete.disconnect(fail_second_batch, sender=CacheEntry)
        self.assertSetEqual(
            set(CacheEntry.objects.values_list("pk", flat=True)),
            {"batch-test-0002", "batch-test-0003"},
        )
        self.assertEqual(delete_in_batches(self.expired()), 2)

    def delete_on_other_connection(self) -> int:
        """Close the thread-local connection even if the test fails."""
        try:
            return delete_in_batches(self.expired(), batch_size=2)
        finally:
            connections.close_all()
