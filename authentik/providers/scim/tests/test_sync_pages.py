"""Full sync page dispatch tests"""

from math import ceil
from unittest.mock import MagicMock, patch

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application, Group, User, UserTypes
from authentik.core.tests.utils import create_test_user
from authentik.lib.generators import generate_id
from authentik.lib.utils.reflection import class_to_path
from authentik.policies.models import PolicyBinding
from authentik.providers.scim.clients.groups import SCIMGroupClient
from authentik.providers.scim.clients.users import SCIMUserClient
from authentik.providers.scim.models import SCIMMapping, SCIMProvider
from authentik.providers.scim.tasks import scim_sync, scim_sync_objects, sync_tasks
from authentik.tenants.models import Tenant


@patch("authentik.providers.scim.clients.base.SCIMClient.can_discover", False)
@patch.object(SCIMUserClient, "write")
@patch.object(SCIMGroupClient, "write")
@patch.object(SCIMUserClient, "delete")
@patch.object(SCIMGroupClient, "delete")
class SCIMSyncPageTests(TestCase):
    """Full sync dispatches pages by primary key range"""

    @apply_blueprint("system/providers-scim.yaml")
    def setUp(self) -> None:
        Tenant.objects.update(avatars="none")
        User.objects.all().exclude_anonymous().delete()
        Group.objects.all().delete()
        self.parent = Group.objects.create(name=generate_id())
        self.child = Group.objects.create(name=generate_id())
        self.child.parents.add(self.parent)

    def _provider(self, page_size: int, bind_group: Group | None = None) -> SCIMProvider:
        provider: SCIMProvider = SCIMProvider.objects.create(
            name=generate_id(),
            url="https://localhost",
            token=generate_id(),
            exclude_users_service_account=True,
            sync_page_size=page_size,
        )
        app = Application.objects.create(name=generate_id(), slug=generate_id())
        if bind_group:
            PolicyBinding.objects.create(target=app, group=bind_group, order=0)
        app.backchannel_providers.add(provider)
        provider.property_mappings.add(
            SCIMMapping.objects.get(managed="goauthentik.io/providers/scim/user")
        )
        provider.property_mappings_group.add(
            SCIMMapping.objects.get(managed="goauthentik.io/providers/scim/group")
        )
        return SCIMProvider.objects.get(pk=provider.pk)

    def _in_scope_users(self, count: int) -> list[int]:
        """Create users in scope of `self.parent`; every other user is also in a descendant
        group, and out-of-scope users and a service account are created in between"""
        pks = []
        for idx in range(count):
            user = create_test_user()
            if idx % 2:
                user.groups.add(self.parent, self.child)
            else:
                user.groups.add(self.child)
            pks.append(user.pk)
            create_test_user()
        create_test_user(type=UserTypes.SERVICE_ACCOUNT).groups.add(self.parent)
        return pks

    @staticmethod
    def _written(mock: MagicMock) -> list:
        return [call.args[0].pk for call in mock.call_args_list]

    def test_sync_paginator_ranges(self, *_):
        """One message per chunk of in-scope pks, bounded by the first and last pk"""
        in_scope = self._in_scope_users(25)
        provider = self._provider(page_size=10, bind_group=self.parent)
        sync_objects = MagicMock()
        sync_tasks.sync_paginator(
            current_task=MagicMock(rel_obj=None),
            provider=provider,
            sync_objects=sync_objects,
            paginator=provider.get_paginator(User),
            object_type=User,
        )
        calls = sync_objects.message_with_options.call_args_list
        self.assertEqual(len(calls), ceil(len(in_scope) / 10))
        expected = [in_scope[i : i + 10] for i in range(0, len(in_scope), 10)]
        for call, chunk in zip(calls, expected, strict=True):
            self.assertEqual(call.kwargs["args"], (class_to_path(User), 1, provider.pk))
            self.assertEqual(call.kwargs["kwargs"], {"pk__gte": chunk[0], "pk__lte": chunk[-1]})

    def test_sync_paginator_empty(self, *_):
        """Without objects in scope, a single empty page is still dispatched"""
        self._in_scope_users(0)
        provider = self._provider(page_size=10, bind_group=self.parent)
        sync_objects = MagicMock()
        sync_tasks.sync_paginator(
            current_task=MagicMock(rel_obj=None),
            provider=provider,
            sync_objects=sync_objects,
            paginator=provider.get_paginator(User),
            object_type=User,
        )
        calls = sync_objects.message_with_options.call_args_list
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].kwargs["kwargs"], {})

    def test_full_sync_writes_each_object_once(self, g_delete, u_delete, g_write, u_write):
        """A full sync writes every in-scope user and group exactly once, and page tasks
        don't run COUNT/OFFSET queries over the full scope"""
        in_scope = self._in_scope_users(25)
        for _ in range(12):
            Group.objects.create(name=generate_id())
        provider = self._provider(page_size=10, bind_group=self.parent)
        u_write.reset_mock()
        g_write.reset_mock()

        with CaptureQueriesContext(connection) as ctx:
            scim_sync.send(provider.pk).get_result()

        self.assertEqual(sorted(self._written(u_write)), in_scope)
        self.assertEqual(
            sorted(self._written(g_write)), sorted(Group.objects.values_list("pk", flat=True))
        )
        user_queries = [
            q["sql"] for q in ctx.captured_queries if 'FROM "authentik_core_user"' in q["sql"]
        ]
        self.assertFalse([sql for sql in user_queries if "OFFSET" in sql])

    def test_full_sync_group_uuid_ranges(self, g_delete, u_delete, g_write, u_write):
        """Group pks are UUIDs; ranges still cover every group exactly once"""
        for _ in range(35):
            Group.objects.create(name=generate_id())
        provider = self._provider(page_size=10)
        g_write.reset_mock()
        scim_sync.send(provider.pk).get_result()
        written = self._written(g_write)
        self.assertEqual(len(written), Group.objects.count())
        self.assertEqual(set(written), set(Group.objects.values_list("pk", flat=True)))

    def test_sync_objects_page_number(self, g_delete, u_delete, g_write, u_write):
        """Messages with a page number and no range (e.g. queued before an upgrade) still
        sync the matching page"""
        in_scope = self._in_scope_users(25)
        provider = self._provider(page_size=10, bind_group=self.parent)
        u_write.reset_mock()
        scim_sync_objects.send(class_to_path(User), 2, provider.pk).get_result()
        self.assertEqual(self._written(u_write), in_scope[10:20])

    def test_sync_objects_range_not_truncated(self, g_delete, u_delete, g_write, u_write):
        """A range holding more objects than the page size (objects created after the pks
        were listed) syncs all of them"""
        in_scope = self._in_scope_users(25)
        provider = self._provider(page_size=10, bind_group=self.parent)
        u_write.reset_mock()
        scim_sync_objects.send(
            class_to_path(User), 1, provider.pk, pk__gte=in_scope[0], pk__lte=in_scope[-1]
        ).get_result()
        self.assertEqual(self._written(u_write), in_scope)
