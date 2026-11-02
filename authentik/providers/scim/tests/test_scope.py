"""Signal-driven SCIM scope reconciliation.

Includes regression scenarios from #26265 (upramod) and #23395 (dominic-r).
"""

import re
from unittest.mock import Mock, patch

from django.core.cache import cache
from django.db import connection, transaction
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from dramatiq.errors import Retry
from requests_mock import Mocker

from authentik.admin.models import SystemSettings
from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import (
    Actor,
    ActorPolicyInheritance,
    Application,
    Group,
    User,
    UserTypes,
)
from authentik.lib.generators import generate_id
from authentik.lib.sync.outgoing.signals import (
    sync_outgoing_dispatch_inhibited,
    sync_outgoing_inhibit_dispatch,
)
from authentik.policies.expression.models import ExpressionPolicy
from authentik.policies.models import PolicyBinding, PolicyEngineMode
from authentik.policies.process import cache_key
from authentik.policies.types import PolicyRequest, PolicyResult
from authentik.providers.scim.clients.groups import SCIMGroupClient
from authentik.providers.scim.clients.users import SCIMUserClient
from authentik.providers.scim.models import SCIMMapping, SCIMProvider, SCIMProviderUser
from authentik.providers.scim.tasks import (
    SCOPE_SYNC_PAGE_SIZE,
    scim_sync_direct,
    scim_sync_direct_dispatch,
    scim_sync_m2m_dispatch,
    scim_sync_scope,
    scim_sync_scope_dispatch,
    scim_sync_user_memberships,
)
from authentik.tasks.models import Task, TaskStatus


class SCIMScopeTests(TestCase):
    """Access changes do not require discovery or a complete provider sync."""

    @apply_blueprint("system/providers-scim.yaml")
    def setUp(self):
        SystemSettings.objects.update(avatars="none")
        with sync_outgoing_inhibit_dispatch():
            User.objects.exclude_anonymous().delete()
            Group.objects.all().delete()
            self.group = Group.objects.create(name=generate_id())
            self.other_group = Group.objects.create(name=generate_id())
            self.exported_group = Group.objects.create(name=generate_id())
            self.user = User.objects.create(username=generate_id())
            self.other_user = User.objects.create(username=generate_id())
            self.group.users.add(self.user)
            self.app = Application.objects.create(name=generate_id(), slug=generate_id())
            self.provider = SCIMProvider.objects.create(
                name=generate_id(), url="https://localhost", token=generate_id()
            )
            self.provider.property_mappings.add(
                SCIMMapping.objects.get(managed="goauthentik.io/providers/scim/user")
            )
            self.provider.group_filters.add(self.exported_group)
            SCIMProvider.objects.filter(pk=self.provider.pk).update(
                backchannel_application=self.app
            )
            self.provider.refresh_from_db()
            self.binding = PolicyBinding.objects.create(target=self.app, group=self.group, order=0)

        self.http = Mocker()
        self.http.start()
        self.addCleanup(self.http.stop)
        self.http.get("https://localhost/ServiceProviderConfig", json={})
        self.http.post(
            "https://localhost/Users",
            json=lambda request, _: request.json() | {"id": f"remote-{request.json()['userName']}"},
            status_code=201,
        )
        self.http.delete(re.compile(r"https://localhost/Users/.*"), status_code=204)
        self.jobs = []
        self.scope_send = scim_sync_scope.send_with_options
        self.dispatch_send = scim_sync_scope_dispatch.send_with_options
        self.memberships = self._patch(scim_sync_user_memberships, "send_with_options")
        self._patch(scim_sync_direct_dispatch, "send")
        self.membership_dispatch = self._patch(scim_sync_m2m_dispatch, "send")
        self._patch(
            scim_sync_scope,
            "send_with_options",
            side_effect=lambda **options: self.jobs.append((scim_sync_scope, options["args"])),
        )
        self._patch(
            scim_sync_scope_dispatch,
            "send_with_options",
            side_effect=lambda **options: self.jobs.append(
                (scim_sync_scope_dispatch, options["args"])
            ),
        )
        self._patch_target(
            "authentik.providers.scim.tasks.CurrentTask.get_task", return_value=Mock()
        )

    def _patch(self, target, attribute, **kwargs):
        patcher = patch.object(target, attribute, **kwargs)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def _patch_target(self, target, **kwargs):
        patcher = patch(target, **kwargs)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def _drain(self):
        count = 0
        while self.jobs:
            actor, args = self.jobs.pop(0)
            actor(*args)
            count += 1
            self.assertLess(count, 1000)

    def _map(self, user=None):
        user = user or self.user
        return SCIMProviderUser.objects.create(
            provider=self.provider, user=user, scim_id=f"remote-{user.username}"
        )

    def _mapped(self, user=None):
        return SCIMProviderUser.objects.filter(
            provider=self.provider, user=user or self.user
        ).exists()

    def test_member_added(self):
        self.group.users.add(self.other_user)
        self._drain()
        self.assertTrue(self._mapped(self.other_user))
        self.assertFalse(self._mapped())
        self.memberships.assert_called_once()

    def test_member_removed(self):
        self._map()
        self.group.users.remove(self.user)
        self._drain()
        self.assertFalse(self._mapped())
        self.assertEqual(self.http.request_history[-1].method, "DELETE")
        self.assertEqual(
            self.http.request_history[-1].headers["Content-Type"], "application/scim+json"
        )

    def test_user_side_membership(self):
        self.other_user.groups.add(self.group)
        self._drain()
        self.assertTrue(self._mapped(self.other_user))
        self.other_user.groups.remove(self.group)
        self._drain()
        self.assertFalse(self._mapped(self.other_user))

    def test_group_clear(self):
        self._map()
        self.group.users.clear()
        self._drain()
        self.assertFalse(self._mapped())
        self.membership_dispatch.assert_called_once_with(
            self.group.pk, "post_remove", [self.user.pk], True
        )

    def test_user_clear(self):
        self._map()
        self.user.groups.clear()
        self._drain()
        self.assertFalse(self._mapped())
        self.membership_dispatch.assert_called_once_with(
            self.user.pk, "post_remove", [self.group.pk], False
        )

    def test_another_binding_preserves_access(self):
        with sync_outgoing_inhibit_dispatch():
            PolicyBinding.objects.create(target=self.app, user=self.user, order=1)
        self._map()
        self.group.users.remove(self.user)
        self._drain()
        self.assertTrue(self._mapped())
        self.assertEqual(self.http.call_count, 0)

    def test_unrelated_membership_does_not_dispatch(self):
        self.other_group.users.add(self.user)
        self.assertEqual(self.jobs, [])

    def test_nested_group_membership(self):
        self.other_group.parents.add(self.group)
        self.other_group.users.add(self.other_user)
        self._drain()
        self.assertTrue(self._mapped(self.other_user))
        self.other_group.users.remove(self.other_user)
        self._drain()
        self.assertFalse(self._mapped(self.other_user))

    def test_group_parentage_changes(self):
        with sync_outgoing_inhibit_dispatch():
            self.other_group.users.add(self.other_user)
        self.other_group.parents.add(self.group)
        self._drain()
        self.assertTrue(self._mapped(self.other_user))
        self.other_group.parents.remove(self.group)
        self._drain()
        self.assertFalse(self._mapped(self.other_user))

    def test_group_parentage_clear(self):
        with sync_outgoing_inhibit_dispatch():
            self.other_group.parents.add(self.group)
            self.other_group.users.add(self.other_user)
        self._map(self.other_user)
        self.group.children.clear()
        self._drain()
        self.assertFalse(self._mapped(self.other_user))

    def test_direct_binding_created(self):
        PolicyBinding.objects.create(target=self.app, user=self.other_user, order=1)
        self._drain()
        self.assertTrue(self._mapped(self.other_user))

    def test_binding_deleted(self):
        with sync_outgoing_inhibit_dispatch():
            binding = PolicyBinding.objects.create(target=self.app, user=self.other_user, order=1)
        self._map(self.other_user)
        binding.delete()
        self._drain()
        self.assertFalse(self._mapped(self.other_user))

    def test_binding_disabled(self):
        with sync_outgoing_inhibit_dispatch():
            PolicyBinding.objects.create(target=self.app, group=self.other_group, order=1)
        self._map()
        self.binding.enabled = False
        self.binding.save()
        self._drain()
        self.assertFalse(self._mapped())

    def test_binding_retargeted(self):
        app = Application.objects.create(name=generate_id(), slug=generate_id())
        self.binding.target = app
        self.binding.save()
        self.assertEqual(self.jobs, [(scim_sync_scope_dispatch, (self.provider.pk,))])

    def test_binding_noop_save(self):
        self.binding.save()
        self.assertEqual(self.jobs, [])

    def test_binding_changes_coalesce_queued_sweep(self):
        self._patch(scim_sync_scope_dispatch, "send_with_options", new=self.dispatch_send)
        self._patch(scim_sync_scope_dispatch.broker.worker, "process_message")
        self.binding.negate = True
        self.binding.save()
        self.binding.enabled = False
        self.binding.save()
        pending = Task.objects.filter(actor_name=scim_sync_scope_dispatch.actor_name)
        self.assertEqual(pending.count(), 1)
        self.assertEqual(pending.get().rel_obj, self.provider)

    def test_running_sweep_does_not_suppress_new_changes(self):
        self._patch(scim_sync_scope_dispatch, "send_with_options", new=self.dispatch_send)
        self._patch(scim_sync_scope_dispatch.broker.worker, "process_message")
        self.binding.negate = True
        self.binding.save()
        Task.objects.filter(actor_name=scim_sync_scope_dispatch.actor_name).update(
            state=TaskStatus.RUNNING
        )
        self.binding.enabled = False
        self.binding.save()
        self.assertEqual(
            Task.objects.filter(actor_name=scim_sync_scope_dispatch.actor_name).count(), 2
        )

    def test_membership_job_rolls_back_with_change(self):
        self._patch(scim_sync_scope, "send_with_options", new=self.scope_send)
        self._patch(scim_sync_scope.broker.worker, "process_message")
        with self.assertRaisesMessage(RuntimeError, "rollback"):
            with transaction.atomic():
                self.group.users.add(self.other_user)
                self.assertTrue(Task.objects.filter(actor_name=scim_sync_scope.actor_name).exists())
                raise RuntimeError("rollback")
        self.assertFalse(Task.objects.filter(actor_name=scim_sync_scope.actor_name).exists())

    def test_application_mode_changed(self):
        with sync_outgoing_inhibit_dispatch():
            PolicyBinding.objects.create(target=self.app, group=self.other_group, order=1)
        self._map()
        self.app.policy_engine_mode = PolicyEngineMode.MODE_ALL
        self.app.save()
        self._drain()
        self.assertFalse(self._mapped())

    def test_application_noop_save(self):
        self.app.save()
        self.assertEqual(self.jobs, [])

    def test_binding_removal_uses_default_access(self):
        self.binding.delete()
        self._drain()
        expected = self.provider.get_object_qs(User).filter(pk=self.other_user.pk).exists()
        self.assertEqual(self._mapped(self.other_user), expected)

    def test_delayed_removal_rechecks_access(self):
        self._map()
        self.group.users.remove(self.user)
        self.group.users.add(self.user)
        self._drain()
        self.assertTrue(self._mapped())
        self.assertEqual(self.http.call_count, 0)

    def test_access_rechecked_under_lock(self):
        self._map()
        self.group.users.remove(self.user)
        original = SCIMUserClient.object_lock

        def change_access(client, user):
            with sync_outgoing_inhibit_dispatch():
                user.groups.add(self.group)
            return original(client, user)

        self._patch(SCIMUserClient, "object_lock", new=change_access)
        self._drain()
        self.assertTrue(self._mapped())
        self.assertFalse(any(request.method == "DELETE" for request in self.http.request_history))

    def test_failed_delete_retains_mapping(self):
        self._map()
        self.http.delete(f"https://localhost/Users/remote-{self.user.username}", status_code=503)
        self.group.users.remove(self.user)
        with self.assertRaises(Retry):
            self._drain()
        self.assertTrue(self._mapped())
        self.http.delete(f"https://localhost/Users/remote-{self.user.username}", status_code=204)
        scim_sync_scope(self.provider.pk, [self.user.pk])
        self.assertFalse(self._mapped())

    def test_already_deleted_user(self):
        self._map()
        self.http.delete(f"https://localhost/Users/remote-{self.user.username}", status_code=404)
        self.group.users.remove(self.user)
        self._drain()
        self.assertFalse(self._mapped())

    def test_dry_run_preserves_mapping(self):
        self._map()
        SCIMProvider.objects.filter(pk=self.provider.pk).update(dry_run=True)
        self.group.users.remove(self.user)
        self._drain()
        self.assertTrue(self._mapped())
        self.assertFalse(any(request.method == "DELETE" for request in self.http.request_history))

    def test_dry_run_does_not_provision(self):
        SCIMProvider.objects.filter(pk=self.provider.pk).update(dry_run=True)
        self.group.users.add(self.other_user)
        self._drain()
        self.assertFalse(self._mapped(self.other_user))
        self.memberships.assert_not_called()

    def test_service_account_exclusion(self):
        User.objects.filter(pk=self.other_user.pk).update(type=UserTypes.SERVICE_ACCOUNT)
        SCIMProvider.objects.filter(pk=self.provider.pk).update(exclude_users_service_account=True)
        self.group.users.add(self.other_user)
        self._drain()
        self.assertFalse(self._mapped(self.other_user))
        self.assertEqual(self.http.call_count, 0)

    def test_duplicate_delivery_does_not_reprovision(self):
        self.group.users.add(self.other_user)
        self._drain()
        count = self.http.call_count
        scim_sync_scope(self.provider.pk, [self.other_user.pk])
        self.assertEqual(self.http.call_count, count)
        self.memberships.assert_called_once()

    def test_followup_failure_rolls_back_mapping(self):
        self.group.users.add(self.other_user)
        self.memberships.side_effect = RuntimeError("enqueue failed")
        with self.assertRaisesMessage(RuntimeError, "enqueue failed"):
            self._drain()
        self.assertFalse(self._mapped(self.other_user))

    def test_nested_inhibition(self):
        with sync_outgoing_inhibit_dispatch():
            with sync_outgoing_inhibit_dispatch():
                pass
            self.assertTrue(sync_outgoing_dispatch_inhibited())
            self.group.users.remove(self.user)
            self.binding.delete()
        self.assertFalse(sync_outgoing_dispatch_inhibited())
        self.assertEqual(self.jobs, [])

    def test_bounded_membership_messages(self):
        users = User.objects.bulk_create(
            [User(username=generate_id()) for _ in range(SCOPE_SYNC_PAGE_SIZE * 2 + 1)]
        )
        self.group.users.add(*users)
        self.assertEqual(len(self.jobs), 3)
        self.assertTrue(all(len(args[1]) <= SCOPE_SYNC_PAGE_SIZE for _, args in self.jobs))

    def test_bounded_clear_messages(self):
        users = User.objects.bulk_create(
            [User(username=generate_id()) for _ in range(SCOPE_SYNC_PAGE_SIZE * 2)]
        )
        with sync_outgoing_inhibit_dispatch():
            self.group.users.add(*users)
        self.group.users.clear()
        self.assertEqual(self.membership_dispatch.call_count, 3)
        self.assertTrue(
            all(
                len(call.args[2]) <= SCOPE_SYNC_PAGE_SIZE
                for call in self.membership_dispatch.call_args_list
            )
        )
        self.assertEqual(len(self.jobs), 3)

    def test_keyset_scope_paging(self):
        with patch("authentik.providers.scim.tasks.SCOPE_SYNC_PAGE_SIZE", 1):
            self.binding.save()
            scim_sync_scope_dispatch(self.provider.pk)
            self._drain()
        self.assertTrue(self._mapped())
        self.assertFalse(self._mapped(self.other_user))

    def test_unchanged_page_has_constant_queries(self):
        users = User.objects.bulk_create([User(username=generate_id()) for _ in range(25)])
        with sync_outgoing_inhibit_dispatch():
            self.group.users.add(*users)
        SCIMProviderUser.objects.bulk_create(
            [
                SCIMProviderUser(provider=self.provider, user=user, scim_id=str(user.pk))
                for user in users
            ]
        )
        scim_sync_scope(self.provider.pk, [users[0].pk])
        with CaptureQueriesContext(connection) as single:
            scim_sync_scope(self.provider.pk, [users[0].pk])
        with CaptureQueriesContext(connection) as page:
            scim_sync_scope(self.provider.pk, [user.pk for user in users])
        self.assertEqual(len(single), len(page))
        self.assertEqual(self.http.call_count, 0)

    def test_dynamic_policy_membership_change(self):
        with sync_outgoing_inhibit_dispatch():
            self.binding.delete()
            policy = ExpressionPolicy.objects.create(
                name=generate_id(),
                expression=(
                    "return request.user.groups.filter(" f'name="{self.other_group.name}").exists()'
                ),
            )
            PolicyBinding.objects.create(target=self.app, policy=policy, order=0)
        self.assertFalse(self.provider.get_object_qs(User, pk=self.other_user.pk).exists())
        self.other_group.users.add(self.other_user)
        self._drain()
        self.assertTrue(self._mapped(self.other_user))
        self.other_group.users.remove(self.other_user)
        self._drain()
        self.assertFalse(self._mapped(self.other_user))

    def _dynamic_membership_policy(self):
        with sync_outgoing_inhibit_dispatch():
            self.binding.delete()
            policy = ExpressionPolicy.objects.create(
                name=generate_id(),
                expression=(
                    f'return request.user.groups.filter(name="{self.other_group.name}").exists()'
                ),
            )
            return PolicyBinding.objects.create(target=self.app, policy=policy, order=0)

    def _mirror_actor(self, parent):
        return Actor.objects.create(
            username=generate_id(),
            type=UserTypes.SERVICE_ACCOUNT,
            parent=parent,
            policy_behavior=ActorPolicyInheritance.MIRROR,
        )

    def test_cached_denial_does_not_skip_membership_repair(self):
        binding = self._dynamic_membership_policy()
        with sync_outgoing_inhibit_dispatch():
            self.exported_group.users.add(self.other_user)
        self.assertFalse(self.provider.get_object_qs(User, pk=self.other_user.pk).exists())
        unrelated_key = cache_key(binding, PolicyRequest(self.user))
        cache.set(unrelated_key, PolicyResult(True))
        with patch.object(cache, "keys", side_effect=AssertionError("unbounded cache scan")):
            self.other_group.users.add(self.other_user)
            self._drain()
        self.assertTrue(self._mapped(self.other_user))
        self.assertTrue(cache.get(unrelated_key).passing)
        with patch.object(SCIMGroupClient, "add_user_to_group") as add:
            scim_sync_user_memberships(self.other_user.pk, self.provider.pk)
        add.assert_called_once_with(self.exported_group, self.other_user.pk)

    def test_cached_allowance_does_not_recreate_revoked_user(self):
        self._dynamic_membership_policy()
        with sync_outgoing_inhibit_dispatch():
            self.other_group.users.add(self.other_user)
        self.assertTrue(self.provider.get_object_qs(User, pk=self.other_user.pk).exists())
        self._map(self.other_user)
        self.other_group.users.remove(self.other_user)
        self._drain()
        self.assertFalse(self._mapped(self.other_user))
        scim_sync_direct("authentik.core.models.User", self.other_user.pk, self.provider.pk)
        self.assertFalse(self._mapped(self.other_user))
        self.assertFalse(self.provider.get_object_qs(User, pk=self.other_user.pk).exists())

    def test_mirror_actor_membership_changes(self):
        with sync_outgoing_inhibit_dispatch():
            actor = self._mirror_actor(self.other_user)
            nested = self._mirror_actor(actor)
        self.group.users.add(self.other_user)
        self._drain()
        self.assertTrue(self._mapped(actor))
        self.assertTrue(self._mapped(nested))
        self.group.users.remove(self.other_user)
        self._drain()
        self.assertFalse(self._mapped(actor))
        self.assertFalse(self._mapped(nested))

    def test_mirror_actor_parentage_changes(self):
        with sync_outgoing_inhibit_dispatch():
            self.other_group.users.add(self.other_user)
            actor = self._mirror_actor(self.other_user)
        self.other_group.parents.add(self.group)
        self._drain()
        self.assertTrue(self._mapped(actor))
        self.other_group.parents.clear()
        self._drain()
        self.assertFalse(self._mapped(actor))

    def test_mirror_actor_clear_membership(self):
        with sync_outgoing_inhibit_dispatch():
            actor = self._mirror_actor(self.user)
        self._map(actor)
        self.user.groups.clear()
        self._drain()
        self.assertFalse(self._mapped(actor))

    def test_bounded_mirror_actor_messages(self):
        page_size = 2
        with sync_outgoing_inhibit_dispatch():
            actors = [self._mirror_actor(self.other_user) for _ in range(5)]
            nested = self._mirror_actor(actors[0])
            independent = self._mirror_actor(self.other_user)
            Actor.objects.filter(pk=independent.pk).update(
                policy_behavior=ActorPolicyInheritance.NONE
            )
        with patch("authentik.providers.scim.signals.SCOPE_SYNC_PAGE_SIZE", page_size):
            self.group.users.add(self.other_user)
        dispatched = {user_pk for _, args in self.jobs for user_pk in args[1]}
        self.assertEqual(
            dispatched, {self.other_user.pk, nested.pk, *(actor.pk for actor in actors)}
        )
        self.assertTrue(all(len(args[1]) <= page_size for _, args in self.jobs))

    def test_mirror_cycle_dispatch_terminates(self):
        with sync_outgoing_inhibit_dispatch():
            actor = self._mirror_actor(self.other_user)
            nested = self._mirror_actor(actor)
            Actor.objects.filter(pk=actor.pk).update(parent=nested)
        self.group.users.add(actor)
        self.assertEqual(len(self.jobs), 1)
        self.assertEqual(set(self.jobs[0][1][1]), {actor.pk, nested.pk})

    def test_mirror_actor_invalidates_effective_user_cache(self):
        binding = self._dynamic_membership_policy()
        with sync_outgoing_inhibit_dispatch():
            actor = self._mirror_actor(self.other_user)
        self.assertFalse(self.provider.get_object_qs(User, pk=actor.pk).exists())
        with sync_outgoing_inhibit_dispatch():
            self.other_group.users.add(self.other_user)
        scim_sync_scope(self.provider.pk, [actor.pk])
        self.assertTrue(self._mapped(actor))
        self.assertIsNone(cache.get(cache_key(binding, PolicyRequest(self.other_user))))
        self.assertTrue(self.provider.get_object_qs(User, pk=actor.pk).exists())

    def test_transaction_rollback_does_not_change_remote(self):
        with self.assertRaisesMessage(RuntimeError, "rollback"):
            with transaction.atomic():
                self.group.users.add(self.other_user)
                raise RuntimeError("rollback")
        self._drain()
        self.assertFalse(self._mapped(self.other_user))
        self.assertEqual(self.http.call_count, 0)
