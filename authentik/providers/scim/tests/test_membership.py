"""SCIM Membership tests"""

from django.test import TestCase
from requests_mock import Mocker

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application, Group, User
from authentik.lib.generators import generate_id
from authentik.providers.scim.clients.schema import ServiceProviderConfiguration
from authentik.providers.scim.models import SCIMMapping, SCIMProvider
from authentik.providers.scim.tasks import scim_sync
from authentik.tenants.models import Tenant


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
    def configure(self) -> None:
        """Configure provider"""
        self.provider: SCIMProvider = SCIMProvider.objects.create(
            name=generate_id(),
            url="https://localhost",
            token=generate_id(),
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
                json=config.model_dump(mode="json"),
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
                json=config.model_dump(mode="json"),
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
                json=config.model_dump(mode="json"),
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
                json=config.model_dump(mode="json"),
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
                json=config.model_dump(mode="json"),
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
                            "path": "members",
                            "value": [{"value": user_scim_id}],
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
                json=config.model_dump(mode="json"),
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
                json=config.model_dump(mode="json"),
            )
            mocker.get(
                f"https://localhost/Groups/{group_scim_id}",
                json={},
            )
            mocker.patch(
                f"https://localhost/Groups/{group_scim_id}",
                json={},
            )
            group.users.add(user)
            group.save()
            self.assertEqual(mocker.call_count, 3)
            self.assertEqual(mocker.request_history[0].method, "PATCH")
            self.assertEqual(mocker.request_history[1].method, "PATCH")
            self.assertEqual(mocker.request_history[2].method, "GET")
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
            self.assertJSONEqual(
                mocker.request_history[1].body,
                {
                    "Operations": [
                        {
                            "op": "replace",
                            "value": {
                                "id": group_scim_id,
                                "displayName": group.name,
                                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                                "externalId": str(group.pk),
                            },
                        }
                    ]
                },
            )

    def test_member_roundtrip(self):
        config = ServiceProviderConfiguration.default()
        # make it behave exactly as it would do in production
        config._is_fallback = False

        user_scim_id = generate_id()
        group_scim_id = generate_id()
        uid = generate_id()
        group = Group.objects.create(
            name=uid,
        )

        user = User.objects.create(username=generate_id())
        # Test initial sync of group creation
        # 1. GET service provider
        # 2. POST create user
        # 3. POST create group (no users)
        with Mocker() as mocker:
            mocker.get(
                "https://localhost/ServiceProviderConfig",
                json=config.model_dump(mode="json"),
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
            self.provider.save()

            scim_sync.send(self.provider.pk)

            self.assertEqual(mocker.call_count, 3)
            self.assertEqual(mocker.request_history[0].method, "GET")
            self.assertEqual(mocker.request_history[0].path, "/serviceproviderconfig")

            self.assertEqual(mocker.request_history[1].method, "POST")
            self.assertEqual(mocker.request_history[1].path, "/users")
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

            self.assertEqual(mocker.request_history[2].method, "POST")
            self.assertEqual(mocker.request_history[2].path, "/groups")
            self.assertJSONEqual(
                mocker.request_history[2].body,
                {
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                    "externalId": str(group.pk),
                    "displayName": group.name,
                },
            )

        # Now we add a user to a group.
        # 1. GET create group to compute group membership diff
        # 2. PUT updating all group attributes at once
        with Mocker(case_sensitive=True) as mocker:
            mocker.put(
                f"https://localhost/Groups/{group_scim_id}",
                json={},
            )
            mocker.get(
                f"https://localhost/Groups/{group_scim_id}",
                json={},
            )

            group.users.add(user)
            self.assertEqual(mocker.request_history[0].method, "PUT")
            self.assertEqual(mocker.request_history[0].path, f"/Groups/{group_scim_id}")
            self.assertJSONEqual(
                mocker.request_history[0].body,
                {
                    "id": group_scim_id,
                    "displayName": group.name,
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                    "members": [{"value": user_scim_id}],
                    "externalId": str(group.pk),
                },
            )

            self.assertEqual(mocker.request_history[1].method, "GET")
            self.assertEqual(mocker.request_history[1].path, f"/Groups/{group_scim_id}")
            self.assertEqual(mocker.call_count, 2)

        # Now we remove a user from a group.
        # 1. GET create group to compute group membership diff
        # 2. PUT updating all group attributes at once
        with Mocker(case_sensitive=True) as mocker:
            mocker.put(
                f"https://localhost/Groups/{group_scim_id}",
                json={},
            )
            mocker.get(
                f"https://localhost/Groups/{group_scim_id}",
                json={},
            )
            group.users.remove(user)
            self.assertEqual(mocker.request_history[0].method, "PUT")
            self.assertEqual(mocker.request_history[0].path, f"/Groups/{group_scim_id}")
            self.assertJSONEqual(
                mocker.request_history[0].body,
                {
                    "id": group_scim_id,
                    "displayName": group.name,
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                    "externalId": str(group.pk),
                },
            )

            self.assertEqual(mocker.request_history[1].method, "GET")
            self.assertEqual(mocker.request_history[1].path, f"/Groups/{group_scim_id}")
            self.assertEqual(mocker.call_count, 2)

    def test_aws_compat_mode(self):
        # A real service provider config to avoid hitting the is_fallback branch
        # in SCIMGroupClient._config#update_group
        sp_config = ServiceProviderConfiguration(
            documentationUri="https://docs.aws.amazon.com/singlesignon/latest/userguide/manage-your-identity-source-idp.html",
            patch=dict(supported=True),
            bulk=dict(supported=False, maxOperations=1),
            filter=dict(supported=True, maxResults=100),
            changePassword=dict(supported=False),
            sort=dict(supported=False),
            authenticationSchemes=[
                dict(
                    name="OAuth Bearer Token",
                    description="Authentication scheme using the OAuth Bearer Token Standard",
                    specUri="https://www.rfc-editor.org/info/rfc6750",
                    documentationUri="https://docs.aws.amazon.com/singlesignon/latest/userguide/provision-automatically.html",
                )
            ],
        )

        user_scim_id = generate_id()
        group_scim_id = generate_id()
        uid = generate_id()
        group = Group.objects.create(
            name=uid,
        )

        user = User.objects.create(username=generate_id())

        # Test initial sync of group creation
        # 1. GET service provider
        # 2. POST create user
        # 3. POST create group (no users)
        with Mocker(case_sensitive=True) as mocker:
            mocker.get(
                "https://localhost/ServiceProviderConfig",
                json=sp_config.model_dump(mode="json"),
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
                    "displayName": group.name,
                },
            )

            self.configure()
            self.provider.compatibility_mode = "aws"
            self.provider.save()

            scim_sync.send(self.provider.pk)

            self.assertEqual(mocker.call_count, 3)
            self.assertEqual(mocker.request_history[0].method, "GET")
            self.assertEqual(mocker.request_history[0].path, "/ServiceProviderConfig")

            self.assertEqual(mocker.request_history[1].method, "POST")
            self.assertEqual(mocker.request_history[1].path, "/Users")
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

            self.assertEqual(mocker.request_history[2].method, "POST")
            self.assertEqual(mocker.request_history[2].path, "/Groups")
            self.assertJSONEqual(
                mocker.request_history[2].body,
                {
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                    "externalId": str(group.pk),
                    "displayName": group.name,
                },
            )

        # Now we add a user to a group.
        # 1. PATCH sending the new member to the group
        with Mocker(case_sensitive=True) as mocker:
            mocker.patch(
                f"https://localhost/Groups/{group_scim_id}",
                json={},
            )

            group.users.add(user)
            self.assertEqual(mocker.call_count, 1)
            self.assertEqual(mocker.request_history[0].method, "PATCH")
            self.assertEqual(mocker.request_history[0].path, f"/Groups/{group_scim_id}")
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

        # Group name changes!
        # 1. PATCH change displayName
        # 2. PATCH change externalId
        # 3. GET user diff -> do nothing, AWS SCIM does not return any members, see: https://docs.aws.amazon.com/singlesignon/latest/developerguide/limitations.html
        with Mocker(case_sensitive=True) as mocker:
            mocker.patch(
                f"https://localhost/Groups/{group_scim_id}",
                json={},
            )
            mocker.get(
                f"https://localhost/Groups/{group_scim_id}",
                json={
                    "id": group_scim_id,
                    "displayName": group.name,
                },
            )

            group.name = "newname" + group.name
            group.save()

            self.assertEqual(mocker.call_count, 3)
            self.assertEqual(mocker.request_history[0].method, "PATCH")
            self.assertEqual(mocker.request_history[0].path, f"/Groups/{group_scim_id}")
            self.assertJSONEqual(
                mocker.request_history[0].body,
                {
                    "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
                    "Operations": [
                        {
                            "op": "replace",
                            "path": "displayName",
                            "value": group.name,
                        }
                    ],
                },
            )

            self.assertEqual(mocker.request_history[1].method, "PATCH")
            self.assertEqual(mocker.request_history[1].path, f"/Groups/{group_scim_id}")
            self.assertJSONEqual(
                mocker.request_history[1].body,
                {
                    "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
                    "Operations": [
                        {
                            "op": "add",
                            "path": "externalId",
                            "value": str(group.pk),
                        }
                    ],
                },
            )

        # Now we add remove the user from a group.
        # 1. PATCH deleting the member from the group
        with Mocker(case_sensitive=True) as mocker:
            mocker.patch(
                f"https://localhost/Groups/{group_scim_id}",
                json={},
            )

            group.users.remove(user)

            self.assertEqual(mocker.call_count, 1)
            self.assertEqual(mocker.request_history[0].method, "PATCH")
            self.assertEqual(mocker.request_history[0].path, f"/Groups/{group_scim_id}")
            self.assertJSONEqual(
                mocker.request_history[0].body,
                {
                    "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
                    "Operations": [
                        {
                            "op": "remove",
                            "path": "members",
                            "value": [{"value": user_scim_id}],
                        }
                    ],
                },
            )
