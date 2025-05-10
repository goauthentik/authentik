"""Test Application Entitlements API"""

from django.urls import reverse
from guardian.shortcuts import assign_perm
from rest_framework.test import APITestCase

from authentik.core.models import Application, ApplicationEntitlement, Group
from authentik.core.tests.utils import create_test_admin_user, create_test_flow, create_test_user
from authentik.crypto.generators import generate_id
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
        self.user.ak_groups.add(group)
        ent = ApplicationEntitlement.objects.create(app=self.app, name=generate_id())
        PolicyBinding.objects.create(target=ent, group=group, order=0)
        ents = self.user.app_entitlements(self.app)
        self.assertEqual(len(ents), 1)
        self.assertEqual(ents[0].name, ent.name)

    def test_group_indirect(self):
        """Test indirect group"""
        parent = Group.objects.create(name=generate_id())
        group = Group.objects.create(name=generate_id(), parent=parent)
        self.user.ak_groups.add(group)
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
        assign_perm("authentik_core.add_applicationentitlement", self.user)
        assign_perm("authentik_core.view_application", self.user)
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
        assign_perm("authentik_core.add_applicationentitlement", self.user)
        assign_perm("authentik_core.view_application", self.user, self.app)
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
        assign_perm("authentik_core.add_applicationentitlement", self.user)
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
