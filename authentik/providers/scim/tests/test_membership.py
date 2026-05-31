"""SCIM Membership tests"""

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
    SCIMProviderUser,
)
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
                            "value": [{"value": user_scim_id, "type": "user"}],
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

    def test_flatten_nested_groups(self):
        """When flatten_nested_groups=True, the parent group's SCIM payload
        includes members of all descendant groups, not just its direct members."""
        config = ServiceProviderConfiguration.default()
        config.patch.supported = True
        parent_scim_id = generate_id()
        child_scim_id = generate_id()
        user_a_scim_id = generate_id()
        user_b_scim_id = generate_id()

        user_a = User.objects.create(username=generate_id())
        user_b = User.objects.create(username=generate_id())

        parent = Group.objects.create(name=generate_id())
        child = Group.objects.create(name=generate_id())
        child.parents.add(parent)

        parent.users.add(user_a)
        child.users.add(user_b)

        with Mocker() as mocker:
            mocker.get(
                "https://localhost/ServiceProviderConfig",
                json=config.model_dump(),
            )
            mocker.post(
                "https://localhost/Users",
                [
                    {"json": {"id": user_a_scim_id}},
                    {"json": {"id": user_b_scim_id}},
                ],
            )
            mocker.post(
                "https://localhost/Groups",
                [
                    {"json": {"id": child_scim_id}},
                    {"json": {"id": parent_scim_id}},
                ],
            )
            mocker.patch(
                f"https://localhost/Groups/{child_scim_id}",
                json={},
            )
            mocker.patch(
                f"https://localhost/Groups/{parent_scim_id}",
                json={},
            )

            self.configure(flatten_nested_groups=True)
            scim_sync.send(self.provider.pk)

            # Resolve the *real* SCIM IDs assigned during sync — the mock returns
            # IDs positionally, which need not match group/user creation order.
            parent_id = SCIMProviderGroup.objects.get(provider=self.provider, group=parent).scim_id
            ua = SCIMProviderUser.objects.get(provider=self.provider, user=user_a).scim_id
            ub = SCIMProviderUser.objects.get(provider=self.provider, user=user_b).scim_id
            # Collect everything PATCHed onto the *parent* group specifically
            # (members may be added across several `add` ops).
            parent_added = set()
            for req in mocker.request_history:
                if req.method != "PATCH" or not req.url.endswith(f"/Groups/{parent_id}"):
                    continue
                for op in req.json().get("Operations", []):
                    if op.get("path") == "members" and op.get("op") == "add":
                        parent_added |= {m["value"] for m in op.get("value", [])}
            self.assertTrue(
                {ua, ub}.issubset(parent_added),
                f"Expected parent to receive its direct member and the nested "
                f"child member, got: {parent_added}",
            )

    def test_flatten_nested_groups_disabled(self):
        """When flatten_nested_groups=False (default), nested members are NOT
        propagated to the parent — only direct members of each group are sent."""
        config = ServiceProviderConfiguration.default()
        config.patch.supported = True
        parent_scim_id = generate_id()
        child_scim_id = generate_id()
        user_a_scim_id = generate_id()
        user_b_scim_id = generate_id()

        user_a = User.objects.create(username=generate_id())
        user_b = User.objects.create(username=generate_id())

        parent = Group.objects.create(name=generate_id())
        child = Group.objects.create(name=generate_id())
        child.parents.add(parent)

        parent.users.add(user_a)
        child.users.add(user_b)

        with Mocker() as mocker:
            mocker.get(
                "https://localhost/ServiceProviderConfig",
                json=config.model_dump(),
            )
            mocker.post(
                "https://localhost/Users",
                [
                    {"json": {"id": user_a_scim_id}},
                    {"json": {"id": user_b_scim_id}},
                ],
            )
            mocker.post(
                "https://localhost/Groups",
                [
                    {"json": {"id": child_scim_id}},
                    {"json": {"id": parent_scim_id}},
                ],
            )
            mocker.patch(
                f"https://localhost/Groups/{child_scim_id}",
                json={},
            )
            mocker.patch(
                f"https://localhost/Groups/{parent_scim_id}",
                json={},
            )

            self.configure()
            scim_sync.send(self.provider.pk)

            parent_id = SCIMProviderGroup.objects.get(provider=self.provider, group=parent).scim_id
            ua = SCIMProviderUser.objects.get(provider=self.provider, user=user_a).scim_id
            ub = SCIMProviderUser.objects.get(provider=self.provider, user=user_b).scim_id
            # Only the *parent* group must not receive the child's member; the
            # child group itself legitimately contains user_b.
            parent_added = set()
            for req in mocker.request_history:
                if req.method != "PATCH" or not req.url.endswith(f"/Groups/{parent_id}"):
                    continue
                for op in req.json().get("Operations", []):
                    if op.get("path") == "members":
                        parent_added |= {m["value"] for m in op.get("value", [])}
            self.assertNotIn(
                ub,
                parent_added,
                f"user_b leaked into parent without flatten enabled: {parent_added}",
            )
            self.assertIn(ua, parent_added)

    def test_flatten_nested_groups_signal_propagates_to_ancestors(self):
        """When flatten_nested_groups=True, adding a user to a child group via
        the M2M signal triggers a membership reconcile on every ancestor group
        too — not just the child."""
        config = ServiceProviderConfiguration.default()
        config.patch.supported = True
        parent_scim_id = generate_id()
        child_scim_id = generate_id()
        user_scim_id = generate_id()

        parent = Group.objects.create(name=generate_id())
        child = Group.objects.create(name=generate_id())
        child.parents.add(parent)

        # First pass: provision groups + (initially member-less) user
        user = User.objects.create(username=generate_id())
        with Mocker() as mocker:
            mocker.get(
                "https://localhost/ServiceProviderConfig",
                json=config.model_dump(),
            )
            mocker.post(
                "https://localhost/Users",
                json={"id": user_scim_id},
            )
            mocker.post(
                "https://localhost/Groups",
                [{"json": {"id": child_scim_id}}, {"json": {"id": parent_scim_id}}],
            )
            self.configure(flatten_nested_groups=True)
            scim_sync.send(self.provider.pk)

        # Second pass: add user to CHILD; expect a PATCH on parent as well
        with Mocker() as mocker:
            mocker.get(
                "https://localhost/ServiceProviderConfig",
                json=config.model_dump(),
            )
            mocker.get(
                f"https://localhost/Groups/{child_scim_id}",
                json={"displayName": child.name, "members": []},
            )
            mocker.get(
                f"https://localhost/Groups/{parent_scim_id}",
                json={"displayName": parent.name, "members": []},
            )
            mocker.patch(
                f"https://localhost/Groups/{child_scim_id}",
                json={},
            )
            mocker.patch(
                f"https://localhost/Groups/{parent_scim_id}",
                json={},
            )
            child.users.add(user)

            parent_id = SCIMProviderGroup.objects.get(provider=self.provider, group=parent).scim_id
            patched_groups = [
                req.url.rsplit("/", 1)[-1]
                for req in mocker.request_history
                if req.method == "PATCH"
            ]
            self.assertIn(
                parent_id,
                patched_groups,
                f"Expected ancestor PATCH; got patches on {patched_groups}",
            )
