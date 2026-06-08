"""Google Workspace outgoing sync signal tests"""

from json import dumps

from django.db import transaction
from django.test import TestCase
from dramatiq.broker import get_broker

from authentik.blueprints.v1.importer import Importer
from authentik.core.models import Application, Group

# Ensure the shared outgoing sync signal handlers are registered.
from authentik.enterprise.providers.google_workspace import signals as _signals  # noqa: F401
from authentik.enterprise.providers.google_workspace.models import GoogleWorkspaceProvider
from authentik.enterprise.providers.google_workspace.tasks import (
    google_workspace_sync_direct_dispatch,
)
from authentik.lib.generators import generate_id
from authentik.tasks.models import Task


class GoogleWorkspaceSignalTests(TestCase):
    """Test outgoing sync signal scheduling behavior."""

    def setUp(self) -> None:
        super().setUp()
        self.provider = GoogleWorkspaceProvider.objects.create(
            name=generate_id(),
            credentials={},
            delegated_subject="",
            default_group_email_domain="goauthentik.io",
        )
        self.app = Application.objects.create(name=generate_id(), slug=generate_id())

    def _without_worker(self):
        broker = get_broker()
        worker = getattr(broker, "worker", None)
        broker.worker = None
        return broker, worker

    def test_unassigned_provider_does_not_dispatch(self):
        """Test an unassigned provider does not schedule direct dispatch."""
        broker, worker = self._without_worker()
        try:
            Group.objects.create(name=generate_id())
        finally:
            broker.worker = worker

        self.assertFalse(
            Task.objects.filter(
                actor_name=google_workspace_sync_direct_dispatch.actor_name
            ).exists()
        )

    def test_direct_dispatch_deduplicates_active_task(self):
        """Test repeated saves only keep one active provider-family dispatch task."""
        self.app.backchannel_providers.add(self.provider)
        broker, worker = self._without_worker()
        try:
            group = Group.objects.create(name=generate_id())
            group.save()
            group.save()
        finally:
            broker.worker = worker

        tasks = Task.objects.filter(actor_name=google_workspace_sync_direct_dispatch.actor_name)
        self.assertEqual(tasks.count(), 1)
        task = tasks.first()
        self.assertTrue(task._deduplicate_by_uid)
        self.assertEqual(
            task._uid,
            f"authentik.core.models.Group:{group.pk}:direct-dispatch",
        )

    def test_rollback_does_not_dispatch_when_not_in_test_mode(self):
        """Test rolled-back saves do not schedule outgoing sync work."""
        self.app.backchannel_providers.add(self.provider)
        broker, worker = self._without_worker()
        try:
            with self.settings(TEST=False):
                with transaction.atomic():
                    Group.objects.create(name=generate_id())
                    transaction.set_rollback(True)
        finally:
            broker.worker = worker

        self.assertFalse(
            Task.objects.filter(
                actor_name=google_workspace_sync_direct_dispatch.actor_name
            ).exists()
        )

    def test_blueprint_validation_does_not_dispatch(self):
        """Test blueprint validation suppresses outgoing sync side effects."""
        self.app.backchannel_providers.add(self.provider)
        group_name = generate_id()
        importer = Importer.from_string(
            dumps(
                {
                    "version": 1,
                    "entries": [
                        {
                            "attrs": {"name": group_name},
                            "identifiers": {"name": group_name},
                            "model": "authentik_core.Group",
                        }
                    ],
                }
            )
        )
        broker, worker = self._without_worker()
        try:
            self.assertTrue(importer.validate()[0])
        finally:
            broker.worker = worker

        self.assertFalse(
            Task.objects.filter(
                actor_name=google_workspace_sync_direct_dispatch.actor_name
            ).exists()
        )
