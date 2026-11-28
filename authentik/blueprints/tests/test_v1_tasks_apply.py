"""Test blueprint apply under concurrent and repeated requests"""

from collections.abc import Callable
from pathlib import Path
from tempfile import NamedTemporaryFile, mkdtemp
from threading import Event, Thread
from time import monotonic
from unittest.mock import patch

from django.db import connection
from django.test import TransactionTestCase

from authentik.blueprints.models import BlueprintInstance, BlueprintInstanceStatus
from authentik.blueprints.v1.hash import blueprint_hash
from authentik.blueprints.v1.importer import Importer
from authentik.blueprints.v1.tasks import (
    _blueprint_lock,
    apply_blueprint,
    blueprints_discovery,
)
from authentik.lib.config import CONFIG
from authentik.lib.generators import generate_id

TMP = mkdtemp("authentik-blueprints")


class TestBlueprintsV1Apply(TransactionTestCase):
    """Test blueprint apply under concurrent and repeated requests"""

    def setUp(self):
        self.file = NamedTemporaryFile(mode="w+", suffix=".yaml", dir=TMP)  # noqa: SIM115
        self.addCleanup(self.file.close)
        self.name = generate_id()
        self.write("initial")
        with CONFIG.patch("blueprints_dir", TMP):
            blueprints_discovery.send()
        self.instance = BlueprintInstance.objects.get(name=self.name)
        self.assertEqual(self.instance.status, BlueprintInstanceStatus.SUCCESSFUL)
        self.applied_hash = self.instance.last_applied_hash

    def write(self, label: str):
        self.file.seek(0)
        self.file.truncate()
        self.file.write(
            f"version: 1\nentries: []\nmetadata:\n  name: {self.name}\n"
            f"context:\n  label: {label}\n"
        )
        self.file.flush()

    def apply(self, only_if_changed: bool = False):
        with CONFIG.patch("blueprints_dir", TMP):
            apply_blueprint.send_with_options(
                args=(self.instance.pk,), kwargs={"only_if_changed": only_if_changed}
            )
        self.instance.refresh_from_db()

    def test_only_if_changed_skips_applied_content(self):
        """Test a duplicate request for already applied content does not apply again"""
        with patch.object(Importer, "apply", autospec=True, return_value=True) as importer:
            self.apply(only_if_changed=True)
            importer.assert_not_called()
            self.apply()
            importer.assert_called_once()

    def test_only_if_changed_applies_changed_content(self):
        """Test a request for changed content still applies it"""
        self.write("changed")
        self.apply(only_if_changed=True)
        self.assertEqual(self.instance.status, BlueprintInstanceStatus.SUCCESSFUL)
        self.assertNotEqual(self.instance.last_applied_hash, self.applied_hash)

    def test_failure_keeps_last_applied_hash(self):
        """Test a failed apply does not record a hash, so discovery keeps retrying it"""
        self.write("changed")
        with patch.object(Importer, "apply", autospec=True, return_value=False):
            self.apply()
        self.assertEqual(self.instance.status, BlueprintInstanceStatus.ERROR)
        self.assertEqual(self.instance.last_applied_hash, self.applied_hash)

    def test_keeps_changes_made_during_apply(self):
        """Test the result of an apply does not overwrite edits made while it ran"""
        context = {"edited": generate_id()}

        def edit_instance(_importer):
            BlueprintInstance.objects.filter(pk=self.instance.pk).update(context=context)
            return True

        with patch.object(Importer, "apply", autospec=True, side_effect=edit_instance):
            self.apply()
        self.assertEqual(self.instance.status, BlueprintInstanceStatus.SUCCESSFUL)
        self.assertEqual(self.instance.context, context)

    def test_does_not_recreate_deleted_instance(self):
        """Test an instance deleted during its apply stays deleted"""

        def delete_instance(_importer):
            BlueprintInstance.objects.filter(pk=self.instance.pk).delete()
            return True

        with patch.object(Importer, "apply", autospec=True, side_effect=delete_instance):
            with CONFIG.patch("blueprints_dir", TMP):
                apply_blueprint.send(self.instance.pk)
        self.assertFalse(BlueprintInstance.objects.filter(pk=self.instance.pk).exists())

    def test_discovery_retries_failed_instance(self):
        """Test discovery retries a failed instance whose hash already matches the file"""
        BlueprintInstance.objects.filter(pk=self.instance.pk).update(
            status=BlueprintInstanceStatus.ERROR
        )
        with CONFIG.patch("blueprints_dir", TMP):
            blueprints_discovery.send(Path(self.file.name).name)
        self.instance.refresh_from_db()
        self.assertEqual(self.instance.status, BlueprintInstanceStatus.SUCCESSFUL)

    def hold_lock(
        self, name: str, hold_for: float, before_release: Callable[[], None] | None = None
    ) -> Thread:
        """Hold a blueprint lock from another database session for `hold_for` seconds"""
        locked = Event()

        def hold():
            try:
                with _blueprint_lock(name) as acquired:
                    self.assertTrue(acquired)
                    locked.set()
                    Event().wait(hold_for)
                    if before_release:
                        before_release()
            finally:
                connection.close()

        holder = Thread(target=hold)
        holder.start()
        self.addCleanup(holder.join)
        self.assertTrue(locked.wait(10))
        return holder

    @CONFIG.patch("worker.task_default_time_limit", "seconds=30")
    def test_waits_for_running_apply(self):
        """Test an apply waits for another apply of the same instance, then runs"""
        self.write("changed")
        start = monotonic()
        self.hold_lock(f"apply/{self.instance.pk}", 2)
        self.apply(only_if_changed=True)
        self.assertGreaterEqual(monotonic() - start, 2)
        self.assertEqual(self.instance.status, BlueprintInstanceStatus.SUCCESSFUL)
        self.assertNotEqual(self.instance.last_applied_hash, self.applied_hash)

    @CONFIG.patch("worker.task_default_time_limit", "seconds=1")
    def test_gives_up_waiting_for_apply(self):
        """Test an apply gives up when the lock is held longer than it may wait"""
        holder = self.hold_lock(f"apply/{self.instance.pk}", 3)
        self.write("changed")
        with patch.object(Importer, "apply", autospec=True, return_value=True) as importer:
            self.apply()
            importer.assert_not_called()
        self.assertEqual(self.instance.last_applied_hash, self.applied_hash)
        holder.join()
        self.apply(only_if_changed=True)
        self.assertNotEqual(self.instance.last_applied_hash, self.applied_hash)

    @CONFIG.patch("worker.task_default_time_limit", "seconds=1")
    def test_discovery_does_not_overlap(self):
        """Test discovery does not run while another discovery holds the lock"""
        self.hold_lock("discovery", 3)
        BlueprintInstance.objects.filter(pk=self.instance.pk).update(
            status=BlueprintInstanceStatus.ERROR
        )
        with CONFIG.patch("blueprints_dir", TMP):
            blueprints_discovery.send()
        self.instance.refresh_from_db()
        self.assertEqual(self.instance.status, BlueprintInstanceStatus.ERROR)

    @CONFIG.patch("worker.task_default_time_limit", "seconds=30")
    def test_skips_content_applied_while_waiting(self):
        """Test an apply that waited for the lock sees the result of the apply holding it,
        and does not apply the same content again"""
        self.write("changed")
        new_hash = blueprint_hash(Path(self.file.name).read_text(encoding="utf-8"))

        def finish_apply():
            BlueprintInstance.objects.filter(pk=self.instance.pk).update(
                status=BlueprintInstanceStatus.SUCCESSFUL, last_applied_hash=new_hash
            )

        self.hold_lock(f"apply/{self.instance.pk}", 1, finish_apply)
        with patch.object(Importer, "apply", autospec=True, return_value=True) as importer:
            self.apply(only_if_changed=True)
            importer.assert_not_called()
        self.assertEqual(self.instance.last_applied_hash, new_hash)

    def test_writes_metadata(self):
        """Test an apply records the blueprint's metadata"""
        BlueprintInstance.objects.filter(pk=self.instance.pk).update(metadata={})
        self.apply()
        self.assertEqual(self.instance.metadata["name"], self.name)

    @CONFIG.patch("worker.task_default_time_limit", "days=60")
    def test_large_time_limit(self):
        """Test a time limit above the largest Postgres lock timeout still works"""
        self.write("changed")
        self.apply(only_if_changed=True)
        self.assertEqual(self.instance.status, BlueprintInstanceStatus.SUCCESSFUL)
        self.assertNotEqual(self.instance.last_applied_hash, self.applied_hash)

    @CONFIG.patch("postgresql.use_pgbouncer", True)
    def test_does_not_wait_behind_transaction_pooler(self):
        """Test the lock is not waited for behind a transaction pooler without a direct
        connection"""
        holder = self.hold_lock(f"apply/{self.instance.pk}", 3)
        self.write("changed")
        start = monotonic()
        with patch.object(Importer, "apply", autospec=True, return_value=True) as importer:
            self.apply()
            importer.assert_not_called()
        self.assertLess(monotonic() - start, 2)
        holder.join()
