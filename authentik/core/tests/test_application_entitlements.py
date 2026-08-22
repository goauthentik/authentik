"""Test Application Entitlements API"""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application, ApplicationEntitlement, Group
from authentik.core.tests.utils import create_test_admin_user, create_test_flow, create_test_user
from authentik.lib.generators import generate_id
from authentik.policies.dummy.models import DummyPolicy
from authentik.policies.models import PolicyBinding
from authentik.providers.oauth2.models import OAuth2Provider


class TestApplicationEntitlements(APITestCase):
    """Test application entitlements"""

    def setUp(self) -> None:
        self.user = create_test_user()
        self.other_user = create_test_user()
        self.provider = OAuth2Provider.objects.create(
            name="test",
            authorization_flow=create_test_flow(),
        )
        self.app: Application = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
            provider=self.provider,
        )

    def test_user(self):
        """Test user-direct assignment"""
        ent = ApplicationEntitlement.objects.create(app=self.app, name=generate_id())
        PolicyBinding.objects.create(target=ent, user=self.user, order=0)
        ents = self.user.app_entitlements(self.app)
        self.assertEqual(len(ents), 1)
        self.assertEqual(ents[0].name, ent.name)

    def test_group(self):
        """Test direct group"""
        group = Group.objects.create(name=generate_id())
        self.user.groups.add(group)
        ent = ApplicationEntitlement.objects.create(app=self.app, name=generate_id())
        PolicyBinding.objects.create(target=ent, group=group, order=0)
        ents = self.user.app_entitlements(self.app)
        self.assertEqual(len(ents), 1)
        self.assertEqual(ents[0].name, ent.name)

    def test_group_indirect(self):
        """Test indirect group"""
        parent = Group.objects.create(name=generate_id())
        group = Group.objects.create(name=generate_id())
        group.parents.add(parent)
        self.user.groups.add(group)
        ent = ApplicationEntitlement.objects.create(app=self.app, name=generate_id())
        PolicyBinding.objects.create(target=ent, group=parent, order=0)
        ents = self.user.app_entitlements(self.app)
        self.assertEqual(len(ents), 1)
        self.assertEqual(ents[0].name, ent.name)

    def test_negate_user(self):
        """Test with negate flag"""
        ent = ApplicationEntitlement.objects.create(app=self.app, name=generate_id())
        PolicyBinding.objects.create(target=ent, user=self.other_user, order=0, negate=True)
        ents = self.user.app_entitlements(self.app)
        self.assertEqual(len(ents), 1)
        self.assertEqual(ents[0].name, ent.name)

    def test_negate_group(self):
        """Test with negate flag"""
        other_group = Group.objects.create(name=generate_id())
        ent = ApplicationEntitlement.objects.create(app=self.app, name=generate_id())
        PolicyBinding.objects.create(target=ent, group=other_group, order=0, negate=True)
        ents = self.user.app_entitlements(self.app)
        self.assertEqual(len(ents), 1)
        self.assertEqual(ents[0].name, ent.name)

    def test_api_perms_global(self):
        """Test API creation with global permissions"""
        self.user.assign_perms_to_managed_role("authentik_core.add_applicationentitlement")
        self.user.assign_perms_to_managed_role("authentik_core.view_application")
        self.client.force_login(self.user)
        res = self.client.post(
            reverse("authentik_api:applicationentitlement-list"),
            data={
                "name": generate_id(),
                "app": self.app.pk,
            },
        )
        self.assertEqual(res.status_code, 201)

    def test_api_perms_scoped(self):
        """Test API creation with scoped permissions"""
        self.user.assign_perms_to_managed_role("authentik_core.add_applicationentitlement")
        self.user.assign_perms_to_managed_role("authentik_core.view_application", self.app)
        self.client.force_login(self.user)
        res = self.client.post(
            reverse("authentik_api:applicationentitlement-list"),
            data={
                "name": generate_id(),
                "app": self.app.pk,
            },
        )
        self.assertEqual(res.status_code, 201)

    def test_api_perms_missing(self):
        """Test API creation with no permissions"""
        self.user.assign_perms_to_managed_role("authentik_core.add_applicationentitlement")
        self.client.force_login(self.user)
        res = self.client.post(
            reverse("authentik_api:applicationentitlement-list"),
            data={
                "name": generate_id(),
                "app": self.app.pk,
            },
        )
        self.assertEqual(res.status_code, 400)
        self.assertJSONEqual(res.content, {"app": ["User does not have access to application."]})

    def test_api_bindings_policy(self):
        """Test that API doesn't allow policies to be bound to this"""
        ent = ApplicationEntitlement.objects.create(app=self.app, name=generate_id())
        policy = DummyPolicy.objects.create(name=generate_id())
        admin = create_test_admin_user()
        self.client.force_login(admin)
        response = self.client.post(
            reverse("authentik_api:policybinding-list"),
            data={
                "target": ent.pbm_uuid,
                "policy": policy.pk,
                "order": 0,
            },
        )
        self.assertJSONEqual(
            response.content.decode(),
            {"non_field_errors": ["One of 'group', 'user' must be set."]},
        )

    def test_api_for_user(self):
        """Test listing all entitlements a user has via for_user"""
        other_app = Application.objects.create(name=generate_id(), slug=generate_id())
        ent_direct = ApplicationEntitlement.objects.create(app=self.app, name=generate_id())
        PolicyBinding.objects.create(target=ent_direct, user=self.user, order=0)
        group = Group.objects.create(name=generate_id())
        self.user.groups.add(group)
        ent_group = ApplicationEntitlement.objects.create(app=other_app, name=generate_id())
        PolicyBinding.objects.create(target=ent_group, group=group, order=0)
        # Entitlement the user does not have
        ApplicationEntitlement.objects.create(app=self.app, name=generate_id())
        self.client.force_login(create_test_admin_user())
        res = self.client.get(
            reverse("authentik_api:applicationentitlement-list"),
            {"for_user": self.user.pk},
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["pagination"]["count"], 2)
        self.assertCountEqual(
            [ent["name"] for ent in body["results"]],
            [ent_direct.name, ent_group.name],
        )
        self.assertCountEqual(
            [ent["app_name"] for ent in body["results"]],
            [self.app.name, other_app.name],
        )

    def test_api_for_user_ordering(self):
        """Test that for_user results can be ordered by application name"""
        app_a = Application.objects.create(name=f"aaa-{generate_id()}", slug=generate_id())
        app_b = Application.objects.create(name=f"bbb-{generate_id()}", slug=generate_id())
        ent_a = ApplicationEntitlement.objects.create(app=app_a, name=generate_id())
        ent_b = ApplicationEntitlement.objects.create(app=app_b, name=generate_id())
        PolicyBinding.objects.create(target=ent_a, user=self.user, order=0)
        PolicyBinding.objects.create(target=ent_b, user=self.user, order=0)
        self.client.force_login(create_test_admin_user())
        for ordering, expected in [
            ("app__name", [ent_a.name, ent_b.name]),
            ("-app__name", [ent_b.name, ent_a.name]),
        ]:
            with self.subTest(ordering=ordering):
                res = self.client.get(
                    reverse("authentik_api:applicationentitlement-list"),
                    {"for_user": self.user.pk, "ordering": ordering, "search": ""},
                )
                self.assertEqual(res.status_code, 200)
                self.assertEqual(
                    [ent["name"] for ent in res.json()["results"]],
                    expected,
                )

    def test_api_for_user_deduplicated(self):
        """Test that an entitlement matched by multiple bindings is only returned once"""
        ent = ApplicationEntitlement.objects.create(app=self.app, name=generate_id())
        PolicyBinding.objects.create(target=ent, user=self.user, order=0)
        group = Group.objects.create(name=generate_id())
        self.user.groups.add(group)
        PolicyBinding.objects.create(target=ent, group=group, order=1)
        self.client.force_login(create_test_admin_user())
        res = self.client.get(
            reverse("authentik_api:applicationentitlement-list"),
            {"for_user": self.user.pk},
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["pagination"]["count"], 1)

    def test_api_for_user_with_permission(self):
        """Test for_user with explicitly granted permissions (non-superuser)"""
        ent = ApplicationEntitlement.objects.create(app=self.app, name=generate_id())
        PolicyBinding.objects.create(target=ent, user=self.user, order=0)
        self.other_user.assign_perms_to_managed_role("authentik_core.view_applicationentitlement")
        self.other_user.assign_perms_to_managed_role("authentik_core.view_user_applications")
        self.client.force_login(self.other_user)
        res = self.client.get(
            reverse("authentik_api:applicationentitlement-list"),
            {"for_user": self.user.pk},
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["pagination"]["count"], 1)
        self.assertEqual(body["results"][0]["name"], ent.name)

    def test_api_for_user_denied(self):
        """Test that for_user requires view_user_applications on the target user"""
        ent = ApplicationEntitlement.objects.create(app=self.app, name=generate_id())
        PolicyBinding.objects.create(target=ent, user=self.user, order=0)
        self.other_user.assign_perms_to_managed_role("authentik_core.view_applicationentitlement")
        self.client.force_login(self.other_user)
        res = self.client.get(
            reverse("authentik_api:applicationentitlement-list"),
            {"for_user": self.user.pk},
        )
        self.assertEqual(res.status_code, 400)
        self.assertJSONEqual(res.content, {"for_user": "User not found"})

    def test_api_for_user_invalid(self):
        """Test for_user with a non-numerical value"""
        self.client.force_login(create_test_admin_user())
        res = self.client.get(
            reverse("authentik_api:applicationentitlement-list"),
            {"for_user": "foo"},
        )
        self.assertEqual(res.status_code, 400)
        self.assertJSONEqual(res.content, {"for_user": "for_user must be numerical"})

    def test_api_bindings_group(self):
        """Test that API doesn't allow policies to be bound to this"""
        ent = ApplicationEntitlement.objects.create(app=self.app, name=generate_id())
        group = Group.objects.create(name=generate_id())
        admin = create_test_admin_user()
        self.client.force_login(admin)
        response = self.client.post(
            reverse("authentik_api:policybinding-list"),
            data={
                "target": ent.pbm_uuid,
                "group": group.pk,
                "order": 0,
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(PolicyBinding.objects.filter(target=ent.pbm_uuid).exists())
