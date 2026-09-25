"""SCIM outgoing synchronization concurrency tests."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from threading import Event, Lock
from unittest.mock import patch

from django.db import close_old_connections
from django.test import TransactionTestCase

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Group
from authentik.lib.generators import generate_id
from authentik.lib.sync.outgoing.base import Direction
from authentik.lib.sync.outgoing.signals import sync_outgoing_inhibit_dispatch
from authentik.providers.scim.clients.groups import SCIMGroupClient
from authentik.providers.scim.models import SCIMMapping, SCIMProvider, SCIMProviderGroup


class SCIMGroupConcurrencyTests(TransactionTestCase):
    """Verify concurrent changes to one group are serialized."""

    @apply_blueprint("system/providers-scim.yaml")
    def setUp(self) -> None:
        self.provider = SCIMProvider.objects.create(
            name=generate_id(),
            url="https://localhost",
            token=generate_id(),
        )
        self.provider.property_mappings_group.set(
            [SCIMMapping.objects.get(managed="goauthentik.io/providers/scim/group")]
        )
        with sync_outgoing_inhibit_dispatch():
            self.group = Group.objects.create(name=generate_id())

    def test_concurrent_create_is_serialized(self):
        """Only one writer creates the remote object and local connection."""
        create_started = Event()
        release_create = Event()
        second_started = Event()
        second_finished = Event()
        create_call_lock = Lock()
        create_calls = 0

        def create(client: SCIMGroupClient, group: Group) -> SCIMProviderGroup:
            nonlocal create_calls
            with create_call_lock:
                create_calls += 1
            create_started.set()
            if not release_create.wait(5):
                raise TimeoutError("Test did not release the first create")
            return SCIMProviderGroup.objects.create(
                provider=client.provider,
                group=group,
                scim_id=generate_id(),
            )

        def write_group(is_second: bool) -> bool:
            close_old_connections()
            try:
                if is_second:
                    second_started.set()
                client = SCIMGroupClient(self.provider)
                _, created = client.write(self.group)
                if is_second:
                    second_finished.set()
                return created
            finally:
                close_old_connections()

        with (
            patch.object(SCIMGroupClient, "create", autospec=True, side_effect=create),
            patch.object(SCIMGroupClient, "update", autospec=True),
            ThreadPoolExecutor(max_workers=2) as executor,
        ):
            first = executor.submit(write_group, False)
            self.assertTrue(create_started.wait(5))
            second = executor.submit(write_group, True)
            self.assertTrue(second_started.wait(5))
            self.assertFalse(second_finished.wait(0.2))
            release_create.set()
            self.assertEqual([first.result(), second.result()], [True, False])

        self.assertEqual(create_calls, 1)
        self.assertEqual(
            SCIMProviderGroup.objects.filter(provider=self.provider, group=self.group).count(),
            1,
        )

    def test_membership_uses_object_lock(self):
        """Membership changes use the same object lock as object writes."""
        client = SCIMGroupClient(self.provider)
        with (
            patch.object(client, "object_lock", return_value=nullcontext()) as object_lock,
            patch.object(client, "update_group") as update_group,
        ):
            client.sync_group_membership(self.group, Direction.add, {1})

        object_lock.assert_called_once_with(self.group)
        update_group.assert_called_once_with(self.group, Direction.add, {1})
