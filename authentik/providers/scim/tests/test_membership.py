"""SCIM Membership tests"""

from unittest.mock import patch

from django.test import TestCase
from requests_mock import Mocker

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application, Group, User
from authentik.lib.generators import generate_id
from authentik.providers.scim.clients.schema import ServiceProviderConfiguration
from authentik.providers.scim.models import (
    SCIMCompatibilityMode,
    SCIMMapping,
    SCIMProvider,
    SCIMProviderGroup,
)
from authentik.providers.scim.tasks import scim_sync
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
