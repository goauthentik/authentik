"""SCIM Membership tests"""

from unittest.mock import patch

from django.test import TestCase
from requests_mock import Mocker

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application, Group, User
from authentik.lib.generators import generate_id
from authentik.lib.sync.outgoing.signals import sync_outgoing_inhibit_dispatch
from authentik.policies.models import PolicyBinding
from authentik.providers.scim.clients.schema import ServiceProviderConfiguration
from authentik.providers.scim.models import (
    SCIMCompatibilityMode,
    SCIMMapping,
    SCIMProvider,
    SCIMProviderGroup,
    SCIMProviderUser,
)
from authentik.providers.scim.tasks import scim_sync, scim_sync_m2m
from authentik.tasks.models import TaskLog
from authentik.tenants.models import Tenant


@patch("authentik.providers.scim.clients.base.SCIMClient.can_discover", False)
class SCIMMembershipTests(TestCase):
    """SCIM Membership tests"""

    provider: SCIMProvider
    app: Application

    def setUp(self) -> None:
        # Delete all users and groups as the mocked HTTP responses only return one ID
        # which will cause errors with multiple users
        User.objects.all().exclude_anonymous().delete()
        Group.objects.all().delete()
        Tenant.objects.update(avatars="none")

    @apply_blueprint("system/providers-scim.yaml")
    def configure(self, **kwargs) -> None:
        """Configure provider"""
        self.provider: SCIMProvider = SCIMProvider.objects.create(
            name=generate_id(),
            url="https://localhost",
            token=generate_id(),
            **kwargs,
        )
        self.app: Application = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        self.app.backchannel_providers.add(self.provider)
        self.provider.save()
        self.provider.property_mappings.set(
            [SCIMMapping.objects.get(managed="goauthentik.io/providers/scim/user")]
        )
        self.provider.property_mappings_group.set(
            [SCIMMapping.objects.get(managed="goauthentik.io/providers/scim/group")]
        )

    def _provision_policy_group_user(self, mock: Mocker):
        """Provision an account whose application access comes from one group."""
        group = Group.objects.create(name=generate_id())
        user = User.objects.create(username=generate_id())
        group.users.add(user)
        user_scim_id = generate_id()
        group_scim_id = generate_id()
        config = ServiceProviderConfiguration.default()
        config.patch.supported = True
        mock.get("https://localhost/ServiceProviderConfig", json=config.model_dump())
        mock.post(
            "https://localhost/Users",
            json=lambda request, _context: request.json() | {"id": user_scim_id},
        )
        mock.post("https://localhost/Groups", json={"id": group_scim_id})

        # Keep the transport double's membership independent of the local database.
        remote_members = set()

        def patch_members(request, _context):
            for operation in request.json()["Operations"]:
                if operation["op"] == "add":
                    remote_members.update(member["value"] for member in operation["value"])
                elif operation["op"] == "remove":
                    self.assertEqual(operation["path"], f'members[value eq "{user_scim_id}"]')
                    remote_members.discard(user_scim_id)
                else:
                    self.fail(f"Unexpected group operation: {operation}")
            return {}

        mock.patch(f"https://localhost/Groups/{group_scim_id}", json=patch_members)
        mock.get(
            f"https://localhost/Groups/{group_scim_id}",
            json=lambda _request, _context: {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                "id": group_scim_id,
                "displayName": group.name,
                "members": [{"value": member} for member in sorted(remote_members)],
            },
        )
        self.configure()
        PolicyBinding.objects.create(target=self.app, group=group, order=0)
        scim_sync.send(self.provider.pk).get_result()
        self.assertTrue(self.provider.get_object_qs(User, pk=user.pk).exists())
        self.assertTrue(
            SCIMProviderUser.objects.filter(
                provider=self.provider, user=user, scim_id=user_scim_id
            ).exists()
        )
        self.assertEqual(remote_members, {user_scim_id})
        self._assert_no_scim_task_errors()
        mock.reset_mock()
        delete_user = mock.delete(f"https://localhost/Users/{user_scim_id}", status_code=204)
        return user, group, delete_user, remote_members

    def _assert_no_scim_task_errors(self):
        """An actor failure must not look like correct account preservation."""
        errors = TaskLog.objects.filter(
            task__actor_name__startswith="authentik.providers.scim.tasks.",
            log_level="error",
            previous=False,
        )
        self.assertFalse(errors.exists(), list(errors.values("task__actor_name", "event")))

    def _assert_policy_group_removal_deprovisions(self, reverse: bool):
        """Exercise the real signal/task chain, with only HTTP transport mocked."""
        with Mocker() as mock:
            user, group, delete_user, _remote_members = self._provision_policy_group_user(mock)
            with self.captureOnCommitCallbacks(execute=True):
                if reverse:
                    group.users.remove(user)
                else:
                    user.groups.remove(group)

            self._assert_no_scim_task_errors()
            self.assertFalse(self.provider.get_object_qs(User, pk=user.pk).exists())
            self.assertTrue(User.objects.filter(pk=user.pk).exists())
            self.assertEqual(
                delete_user.call_count,
                1,
                "Leaving application scope must deprovision the managed SCIM account "
                "without a manual or scheduled full sync.",
            )
            self.assertFalse(
                SCIMProviderUser.objects.filter(provider=self.provider, user=user).exists()
            )

    def test_policy_group_removal_deprovisions_user(self):
        """Removing from the group's manager must deprovision the scoped user."""
        self._assert_policy_group_removal_deprovisions(reverse=True)

    def test_policy_group_removal_from_user_deprovisions_user(self):
        """Removing from the user's manager must also deprovision the scoped user."""
        self._assert_policy_group_removal_deprovisions(reverse=False)

    def test_policy_group_removal_manual_sync_cleanup(self):
        """Control: a full sync can remove the same out-of-scope managed account."""
        with Mocker() as mock:
            user, group, delete_user, _remote_members = self._provision_policy_group_user(mock)
            with self.captureOnCommitCallbacks(execute=True):
                group.users.remove(user)
            scim_sync.send(self.provider.pk).get_result()
            self._assert_no_scim_task_errors()
            self.assertEqual(delete_user.call_count, 1)
            self.assertFalse(
                SCIMProviderUser.objects.filter(provider=self.provider, user=user).exists()
            )

    def test_policy_group_removal_preserves_directly_bound_user(self):
        """A remaining direct binding must preserve the managed account."""
        with Mocker() as mock:
            user, group, delete_user, remote_members = self._provision_policy_group_user(mock)
            PolicyBinding.objects.create(target=self.app, user=user, order=1)
            with self.captureOnCommitCallbacks(execute=True):
                group.users.remove(user)
            self._assert_no_scim_task_errors()
            self.assertTrue(self.provider.get_object_qs(User, pk=user.pk).exists())
            self.assertEqual(
                remote_members, set(), "The membership event must reach the SCIM target."
            )
            self.assertEqual(delete_user.call_count, 0)
            self.assertTrue(
                SCIMProviderUser.objects.filter(provider=self.provider, user=user).exists()
            )

    def test_policy_group_removal_preserves_other_group_binding(self):
        """Another group may still grant the user access to the application."""
        with Mocker() as mock:
            user, group, delete_user, remote_members = self._provision_policy_group_user(mock)
            with sync_outgoing_inhibit_dispatch():
                other_group = Group.objects.create(name=generate_id())
                other_group.users.add(user)
            PolicyBinding.objects.create(target=self.app, group=other_group, order=1)

            with self.captureOnCommitCallbacks(execute=True):
                group.users.remove(user)

            self._assert_no_scim_task_errors()
            self.assertTrue(self.provider.get_object_qs(User, pk=user.pk).exists())
            self.assertEqual(remote_members, set())
            self.assertEqual(delete_user.call_count, 0)
            self.assertTrue(
                SCIMProviderUser.objects.filter(provider=self.provider, user=user).exists()
            )

    def test_policy_group_removal_with_filtered_group(self):
        """Group sync filters must not suppress account deprovisioning."""
        with Mocker() as mock:
            user, group, delete_user, _remote_members = self._provision_policy_group_user(mock)
            with sync_outgoing_inhibit_dispatch():
                other_group = Group.objects.create(name=generate_id())
            self.provider.group_filters.add(other_group)
            self.assertFalse(self.provider.get_object_qs(Group, pk=group.pk).exists())

            with self.captureOnCommitCallbacks(execute=True):
                group.users.remove(user)

            self._assert_no_scim_task_errors()
            self.assertFalse(self.provider.get_object_qs(User, pk=user.pk).exists())
            self.assertEqual(delete_user.call_count, 1)
            self.assertFalse(
                SCIMProviderUser.objects.filter(provider=self.provider, user=user).exists()
            )

    def test_policy_group_removal_without_group_mapping(self):
        """User cleanup must work even when the group has no remote mapping."""
        with Mocker() as mock:
            user, group, delete_user, _remote_members = self._provision_policy_group_user(mock)
            SCIMProviderGroup.objects.filter(provider=self.provider, group=group).delete()

            with self.captureOnCommitCallbacks(execute=True):
                group.users.remove(user)

            self._assert_no_scim_task_errors()
            self.assertFalse(self.provider.get_object_qs(User, pk=user.pk).exists())
            self.assertEqual(delete_user.call_count, 1)
            self.assertFalse(
                SCIMProviderUser.objects.filter(provider=self.provider, user=user).exists()
            )

    def test_policy_group_removal_remote_group_not_found(self):
        """An absent remote group must not block cleanup of its former user."""
        with Mocker() as mock:
            user, group, delete_user, _remote_members = self._provision_policy_group_user(mock)
            group_mapping = SCIMProviderGroup.objects.get(provider=self.provider, group=group)
            mock.patch(f"https://localhost/Groups/{group_mapping.scim_id}", status_code=404)

            with self.captureOnCommitCallbacks(execute=True):
                group.users.remove(user)

            self._assert_no_scim_task_errors()
            self.assertFalse(self.provider.get_object_qs(User, pk=user.pk).exists())
            self.assertEqual(delete_user.call_count, 1)
            self.assertFalse(
                SCIMProviderUser.objects.filter(provider=self.provider, user=user).exists()
            )

    def test_policy_group_removal_preserves_readded_user(self):
        """A delayed removal event must recheck current application access."""
        with Mocker() as mock:
            user, group, delete_user, _remote_members = self._provision_policy_group_user(mock)
            # Simulate the worker handling removal after the user has been re-added.
            with sync_outgoing_inhibit_dispatch():
                group.users.remove(user)
                group.users.add(user)

            scim_sync_m2m.send(group.pk, self.provider.pk, "post_remove", [user.pk]).get_result()

            self._assert_no_scim_task_errors()
            self.assertTrue(self.provider.get_object_qs(User, pk=user.pk).exists())
            self.assertEqual(delete_user.call_count, 0)
            self.assertTrue(
                SCIMProviderUser.objects.filter(provider=self.provider, user=user).exists()
            )

    def test_policy_group_removal_only_cleans_affected_user(self):
        """An event must not sweep unrelated out-of-scope account mappings."""
        with Mocker() as mock:
            user, group, delete_user, _remote_members = self._provision_policy_group_user(mock)
            with sync_outgoing_inhibit_dispatch():
                unrelated_user = User.objects.create(username=generate_id())
            unrelated_id = generate_id()
            SCIMProviderUser.objects.create(
                provider=self.provider, user=unrelated_user, scim_id=unrelated_id
            )
            delete_unrelated = mock.delete(
                f"https://localhost/Users/{unrelated_id}", status_code=204
            )
            self.assertFalse(self.provider.get_object_qs(User, pk=unrelated_user.pk).exists())

            with self.captureOnCommitCallbacks(execute=True):
                group.users.remove(user)

            self._assert_no_scim_task_errors()
            self.assertEqual(delete_user.call_count, 1)
            self.assertEqual(delete_unrelated.call_count, 0)
            self.assertTrue(
                SCIMProviderUser.objects.filter(
                    provider=self.provider, user=unrelated_user, scim_id=unrelated_id
                ).exists()
            )

    def test_policy_group_removal_delete_retry(self):
        """A failed remote delete must retain the mapping for a successful retry."""
        with Mocker() as mock:
            user, group, _delete_user, _remote_members = self._provision_policy_group_user(mock)
            mapping = SCIMProviderUser.objects.get(provider=self.provider, user=user)
            delete_user = mock.delete(
                f"https://localhost/Users/{mapping.scim_id}",
                [{"status_code": 429}, {"status_code": 204}],
            )

            with self.captureOnCommitCallbacks(execute=True):
                group.users.remove(user)

            self.assertFalse(self.provider.get_object_qs(User, pk=user.pk).exists())
            self.assertEqual(delete_user.call_count, 1)
            self.assertTrue(SCIMProviderUser.objects.filter(pk=mapping.pk).exists())
            self.assertTrue(
                TaskLog.objects.filter(
                    task__actor_name=scim_sync_m2m.actor_name,
                    event__startswith="Task has encountered an error and will be retried",
                    previous=False,
                ).exists()
            )

            scim_sync_m2m.send(group.pk, self.provider.pk, "post_remove", [user.pk]).get_result()

            self.assertEqual(delete_user.call_count, 2)
            self.assertFalse(SCIMProviderUser.objects.filter(pk=mapping.pk).exists())

    def test_policy_group_removal_remote_user_not_found(self):
        """A remote account that is already gone needs no further cleanup."""
        with Mocker() as mock:
            user, group, _delete_user, _remote_members = self._provision_policy_group_user(mock)
            mapping = SCIMProviderUser.objects.get(provider=self.provider, user=user)
            delete_user = mock.delete(f"https://localhost/Users/{mapping.scim_id}", status_code=404)

            with self.captureOnCommitCallbacks(execute=True):
                group.users.remove(user)

            self._assert_no_scim_task_errors()
            self.assertEqual(delete_user.call_count, 1)
            self.assertFalse(SCIMProviderUser.objects.filter(pk=mapping.pk).exists())

    def test_policy_group_removal_dry_run_preserves_mapping(self):
        """Dry-run processing must leave both the remote account and its mapping."""
        with Mocker() as mock:
            user, group, delete_user, remote_members = self._provision_policy_group_user(mock)
            mapping = SCIMProviderUser.objects.get(provider=self.provider, user=user)
            self.provider.dry_run = True
            self.provider.save()

            with self.captureOnCommitCallbacks(execute=True):
                group.users.remove(user)

            self._assert_no_scim_task_errors()
            self.assertFalse(self.provider.get_object_qs(User, pk=user.pk).exists())
            self.assertEqual(delete_user.call_count, 0)
            self.assertEqual(remote_members, {mapping.scim_id})
            self.assertFalse(
                any(
                    request.method in {"POST", "PUT", "PATCH", "DELETE"}
                    for request in mock.request_history
                )
            )
            self.assertTrue(SCIMProviderUser.objects.filter(pk=mapping.pk).exists())

    def test_member_add(self):
        """Test member add"""
        config = ServiceProviderConfiguration.default()

        config.patch.supported = True
        user_scim_id = generate_id()
        group_scim_id = generate_id()
        uid = generate_id()
        group = Group.objects.create(
            name=uid,
        )

        user = User.objects.create(username=generate_id())

        with Mocker() as mocker:
            mocker.get(
                "https://localhost/ServiceProviderConfig",
                json=config.model_dump(),
            )
            mocker.post(
                "https://localhost/Users",
                json={
                    "id": user_scim_id,
                },
            )
            mocker.post(
                "https://localhost/Groups",
                json={
                    "id": group_scim_id,
                },
            )

            self.configure()
            scim_sync.send(self.provider.pk)

            self.assertEqual(mocker.call_count, 3)
            self.assertEqual(mocker.request_history[0].method, "GET")
            self.assertEqual(mocker.request_history[1].method, "POST")
            self.assertEqual(mocker.request_history[2].method, "POST")
            self.assertJSONEqual(
                mocker.request_history[1].body,
                {
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                    "emails": [],
                    "active": True,
                    "externalId": user.uid,
                    "name": {"familyName": " ", "formatted": " ", "givenName": ""},
                    "displayName": "",
                    "userName": user.username,
                },
            )
            self.assertJSONEqual(
                mocker.request_history[2].body,
                {
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                    "externalId": str(group.pk),
                    "displayName": group.name,
                },
            )

        with Mocker() as mocker:
            mocker.get(
                "https://localhost/ServiceProviderConfig",
                json=config.model_dump(),
            )
            mocker.patch(
                f"https://localhost/Groups/{group_scim_id}",
                json={},
            )
            group.users.add(user)
            self.assertEqual(mocker.call_count, 1)
            self.assertEqual(mocker.request_history[0].method, "PATCH")
            self.assertJSONEqual(
                mocker.request_history[0].body,
                {
                    "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
                    "Operations": [
                        {
                            "op": "add",
                            "path": "members",
                            "value": [{"value": user_scim_id}],
                        }
                    ],
                },
            )

    def test_member_remove(self):
        """Test member remove"""
        config = ServiceProviderConfiguration.default()

        config.patch.supported = True
        user_scim_id = generate_id()
        group_scim_id = generate_id()
        uid = generate_id()
        group = Group.objects.create(
            name=uid,
        )

        user = User.objects.create(username=generate_id())

        with Mocker() as mocker:
            mocker.get(
                "https://localhost/ServiceProviderConfig",
                json=config.model_dump(),
            )
            mocker.post(
                "https://localhost/Users",
                json={
                    "id": user_scim_id,
                },
            )
            mocker.post(
                "https://localhost/Groups",
                json={
                    "id": group_scim_id,
                },
            )

            self.configure()
            scim_sync.send(self.provider.pk)

            self.assertEqual(mocker.call_count, 3)
            self.assertEqual(mocker.request_history[0].method, "GET")
            self.assertEqual(mocker.request_history[1].method, "POST")
            self.assertEqual(mocker.request_history[2].method, "POST")
            self.assertJSONEqual(
                mocker.request_history[1].body,
                {
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                    "active": True,
                    "displayName": "",
                    "emails": [],
                    "externalId": user.uid,
                    "name": {"familyName": " ", "formatted": " ", "givenName": ""},
                    "userName": user.username,
                },
            )
            self.assertJSONEqual(
                mocker.request_history[2].body,
                {
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                    "externalId": str(group.pk),
                    "displayName": group.name,
                },
            )

        with Mocker() as mocker:
            mocker.get(
                "https://localhost/ServiceProviderConfig",
                json=config.model_dump(),
            )
            mocker.patch(
                f"https://localhost/Groups/{group_scim_id}",
                json={},
            )
            group.users.add(user)
            self.assertEqual(mocker.call_count, 1)
            self.assertEqual(mocker.request_history[0].method, "PATCH")
            self.assertJSONEqual(
                mocker.request_history[0].body,
                {
                    "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
                    "Operations": [
                        {
                            "op": "add",
                            "path": "members",
                            "value": [{"value": user_scim_id}],
                        }
                    ],
                },
            )

        with Mocker() as mocker:
            mocker.get(
                "https://localhost/ServiceProviderConfig",
                json=config.model_dump(),
            )
            mocker.patch(
                f"https://localhost/Groups/{group_scim_id}",
                json={},
            )
            group.users.remove(user)
            self.assertEqual(mocker.call_count, 1)
            self.assertEqual(mocker.request_history[0].method, "PATCH")
            self.assertJSONEqual(
                mocker.request_history[0].body,
                {
                    "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
                    "Operations": [
                        {
                            "op": "remove",
                            "path": f'members[value eq "{user_scim_id}"]',
                        }
                    ],
                },
            )

    def test_member_remove_last_without_patch(self):
        """Test removing a group's last member without PATCH support, against a server which
        does not echo members in write responses"""
        user_scim_id = generate_id()
        group_scim_id = generate_id()
        group = Group.objects.create(name=generate_id())
        user = User.objects.create(username=generate_id())
        group.users.add(user)

        with Mocker() as mocker:
            mocker.post("https://localhost/Users", json={"id": user_scim_id})
            mocker.post("https://localhost/Groups", json={"id": group_scim_id})

            self.configure(compatibility_mode=SCIMCompatibilityMode.VCENTER)
            scim_sync.send(self.provider.pk)

            # The create request already contains the members, no separate PATCH is sent
            self.assertEqual(
                [request.method for request in mocker.request_history], ["POST", "POST"]
            )
            self.assertJSONEqual(
                mocker.request_history[1].body,
                {
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                    "externalId": str(group.pk),
                    "displayName": group.name,
                    "members": [{"value": user_scim_id}],
                },
            )

        with Mocker() as mocker:
            mocker.put(f"https://localhost/Groups/{group_scim_id}", status_code=204)
            mocker.get(
                f"https://localhost/Groups/{group_scim_id}",
                json={
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                    "id": group_scim_id,
                    "externalId": str(group.pk),
                    "displayName": group.name,
                    "members": [],
                },
            )

            group.users.remove(user)

            self.assertEqual([request.method for request in mocker.request_history], ["PUT", "GET"])
            self.assertJSONEqual(
                mocker.request_history[0].body,
                {
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                    "id": group_scim_id,
                    "externalId": str(group.pk),
                    "displayName": group.name,
                    "members": [],
                },
            )

    def test_group_write_without_recorded_members(self):
        """Test that a group whose recorded state has no member list is written again"""
        user_scim_id = generate_id()
        group_scim_id = generate_id()
        group = Group.objects.create(name=generate_id())
        user = User.objects.create(username=generate_id())
        group.users.add(user)

        with Mocker() as mocker:
            mocker.post("https://localhost/Users", json={"id": user_scim_id})
            mocker.post("https://localhost/Groups", json={"id": group_scim_id})

            self.configure(compatibility_mode=SCIMCompatibilityMode.VCENTER)
            scim_sync.send(self.provider.pk)

        # Simulate a connection recorded by a version which did not store the member list
        connection = SCIMProviderGroup.objects.get(provider=self.provider, group=group)
        connection.attributes.pop("members")
        connection.save()

        with Mocker() as mocker:
            remote_group = {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                "id": group_scim_id,
                "externalId": str(group.pk),
                "displayName": group.name,
                "members": [{"value": user_scim_id}],
            }
            mocker.put(f"https://localhost/Groups/{group_scim_id}", json=remote_group)
            mocker.get(f"https://localhost/Groups/{group_scim_id}", json=remote_group)

            group.save()

            self.assertEqual([request.method for request in mocker.request_history], ["PUT", "GET"])
            self.assertJSONEqual(
                mocker.request_history[0].body,
                {
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                    "id": group_scim_id,
                    "externalId": str(group.pk),
                    "displayName": group.name,
                    "members": [{"value": user_scim_id}],
                },
            )

    def test_member_remove_only_in_remote_group(self):
        """Test member remove of a member that only exists in the remote group"""
        user_scim_id = generate_id()
        stale_scim_id = generate_id()
        group_scim_id = generate_id()
        group = Group.objects.create(name=generate_id())
        user = User.objects.create(username=generate_id())
        group.users.add(user)
        remote_group = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "id": group_scim_id,
            "externalId": str(group.pk),
            "displayName": group.name,
            "members": [{"value": user_scim_id}],
        }

        with Mocker() as mocker:
            mocker.post("https://localhost/Users", json={"id": user_scim_id})
            mocker.post("https://localhost/Groups", json=remote_group)

            self.configure(compatibility_mode=SCIMCompatibilityMode.VCENTER)
            scim_sync.send(self.provider.pk)

        with Mocker() as mocker:
            mocker.get(
                f"https://localhost/Groups/{group_scim_id}",
                json=remote_group
                | {"members": [{"value": x} for x in (user_scim_id, stale_scim_id)]},
            )
            mocker.patch(f"https://localhost/Groups/{group_scim_id}", json={})

            group.save()

            self.assertEqual(
                [request.method for request in mocker.request_history], ["GET", "PATCH"]
            )
            self.assertJSONEqual(
                mocker.request_history[1].body,
                {
                    "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
                    "Operations": [
                        {
                            "op": "remove",
                            "path": f'members[value eq "{stale_scim_id}"]',
                        }
                    ],
                },
            )

    def test_member_add_save(self):
        """Test member add + save"""
        config = ServiceProviderConfiguration.default()

        config.patch.supported = True
        user_scim_id = generate_id()
        group_scim_id = generate_id()
        uid = generate_id()
        group = Group.objects.create(
            name=uid,
        )

        user = User.objects.create(username=generate_id())

        # Test initial sync of group creation
        with Mocker() as mocker:
            mocker.get(
                "https://localhost/ServiceProviderConfig",
                json=config.model_dump(),
            )
            mocker.post(
                "https://localhost/Users",
                json={
                    "id": user_scim_id,
                },
            )
            mocker.post(
                "https://localhost/Groups",
                json={
                    "id": group_scim_id,
                },
            )

            self.configure()
            scim_sync.send(self.provider.pk)

            self.assertEqual(mocker.call_count, 3)
            self.assertEqual(mocker.request_history[0].method, "GET")
            self.assertEqual(mocker.request_history[1].method, "POST")
            self.assertEqual(mocker.request_history[2].method, "POST")
            self.assertJSONEqual(
                mocker.request_history[1].body,
                {
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                    "emails": [],
                    "active": True,
                    "externalId": user.uid,
                    "name": {"familyName": " ", "formatted": " ", "givenName": ""},
                    "displayName": "",
                    "userName": user.username,
                },
            )
            self.assertJSONEqual(
                mocker.request_history[2].body,
                {
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                    "externalId": str(group.pk),
                    "displayName": group.name,
                },
            )

        with Mocker() as mocker:
            mocker.get(
                "https://localhost/ServiceProviderConfig",
                json=config.model_dump(),
            )
            mocker.get(
                f"https://localhost/Groups/{group_scim_id}",
                json={
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                    "id": group_scim_id,
                    "externalId": str(group.pk),
                    "displayName": group.name,
                    "members": [{"value": user_scim_id}],
                },
            )
            mocker.patch(
                f"https://localhost/Groups/{group_scim_id}",
                json={},
            )
            group.users.add(user)
            group.save()
            # The save does not write the group again, as nothing besides the members changed,
            # so it only compares the members against the remote state
            self.assertEqual(
                [request.method for request in mocker.request_history], ["PATCH", "GET"]
            )
            self.assertJSONEqual(
                mocker.request_history[0].body,
                {
                    "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
                    "Operations": [
                        {
                            "op": "add",
                            "path": "members",
                            "value": [{"value": user_scim_id}],
                        }
                    ],
                },
            )

    def test_member_add_save_compat_webex(self):
        """Test member add + save"""
        config = ServiceProviderConfiguration.default()

        config.patch.supported = True
        user_scim_id = generate_id()
        group_scim_id = generate_id()
        uid = generate_id()
        group = Group.objects.create(
            name=uid,
        )

        user = User.objects.create(username=generate_id())

        # Test initial sync of group creation
        with Mocker() as mocker:
            mocker.get(
                "https://localhost/ServiceProviderConfig",
                json=config.model_dump(),
            )
            mocker.post(
                "https://localhost/Users",
                json={
                    "id": user_scim_id,
                },
            )
            mocker.post(
                "https://localhost/Groups",
                json={
                    "id": group_scim_id,
                },
            )

            self.configure(compatibility_mode=SCIMCompatibilityMode.WEBEX)
            scim_sync.send(self.provider.pk)

            self.assertEqual(mocker.call_count, 3)
            self.assertEqual(mocker.request_history[0].method, "GET")
            self.assertEqual(mocker.request_history[1].method, "POST")
            self.assertEqual(mocker.request_history[2].method, "POST")
            self.assertJSONEqual(
                mocker.request_history[1].body,
                {
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                    "emails": [],
                    "active": True,
                    "externalId": user.uid,
                    "name": {"familyName": " ", "formatted": " ", "givenName": ""},
                    "displayName": "",
                    "userName": user.username,
                },
            )
            self.assertJSONEqual(
                mocker.request_history[2].body,
                {
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                    "externalId": str(group.pk),
                    "displayName": group.name,
                },
            )

        with Mocker() as mocker:
            mocker.get(
                "https://localhost/ServiceProviderConfig",
                json=config.model_dump(),
            )
            mocker.get(
                f"https://localhost/Groups/{group_scim_id}",
                json={
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                    "id": group_scim_id,
                    "externalId": str(group.pk),
                    "displayName": group.name,
                    "members": [{"value": user_scim_id}],
                },
            )
            mocker.patch(
                f"https://localhost/Groups/{group_scim_id}",
                json={},
            )
            group.users.add(user)
            group.save()
            # The save does not write the group again, as nothing besides the members changed,
            # so it only compares the members against the remote state
            self.assertEqual(
                [request.method for request in mocker.request_history], ["PATCH", "GET"]
            )
            self.assertJSONEqual(
                mocker.request_history[0].body,
                {
                    "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
                    "Operations": [
                        {
                            "op": "add",
                            "path": "members",
                            "value": [{"value": user_scim_id, "type": "user"}],
                        }
                    ],
                },
            )
