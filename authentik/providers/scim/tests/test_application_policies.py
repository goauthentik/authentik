"""SCIM Application Policies tests"""

from django.test import TestCase

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application, Group, User
from authentik.lib.generators import generate_id
from authentik.policies.models import PolicyBinding
from authentik.providers.scim.models import SCIMMapping, SCIMProvider
from authentik.tenants.models import Tenant


class SCIMApplicationPoliciesTests(TestCase):
    """SCIM Application Policies tests"""

    @apply_blueprint("system/providers-scim.yaml")
    def setUp(self) -> None:
        # Delete all users and groups as to only have the test users and groups
        User.objects.all().exclude_anonymous().delete()
        Group.objects.all().delete()
        Tenant.objects.update(avatars="none")

        self.provider: SCIMProvider = SCIMProvider.objects.create(
            name=generate_id(),
            url="https://localhost",
            token=generate_id(),
            exclude_users_service_account=True,
        )
        self.provider.property_mappings.add(
            SCIMMapping.objects.get(managed="goauthentik.io/providers/scim/user")
        )
        self.provider.property_mappings_group.add(
            SCIMMapping.objects.get(managed="goauthentik.io/providers/scim/group")
        )

        self.app: Application = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        self.app.backchannel_providers.add(self.provider)

        self.group1 = Group.objects.create(name="group-1")
        self.group2 = Group.objects.create(name="group-2")
        self.group3 = Group.objects.create(name="group-3")

        self.users = {}
        for i in range(1, 5):
            uid = generate_id()
            self.users[i] = User.objects.create(
                username=uid,
                name=f"{uid} User",
                email=f"{uid}@goauthentik.io",
            )

        self.users[1].ak_groups.add(self.group1)
        self.users[2].ak_groups.add(self.group2)
        self.users[4].ak_groups.add(self.group1)
        self.users[4].ak_groups.add(self.group2)

    def test_no_group_policy(self):
        """Test with no group policy set"""
        user_qs = self.provider.get_object_qs(User)

        self.assertEqual(
            set([self.users[1].pk, self.users[2].pk, self.users[3].pk, self.users[4].pk]),
            set(user_qs.values_list("pk", flat=True)),
        )

    def test_single_group_policy(self):
        """Test with one group policy set"""
        PolicyBinding.objects.create(target=self.app, group=self.group1, order=0)

        user_qs = self.provider.get_object_qs(User)

        self.assertEqual(
            set([self.users[1].pk, self.users[4].pk]),
            set(user_qs.values_list("pk", flat=True)),
        )

    def test_multiple_group_policies(self):
        """Test with multiple group policies set"""
        PolicyBinding.objects.create(target=self.app, group=self.group1, order=0)
        PolicyBinding.objects.create(target=self.app, group=self.group2, order=0)

        user_qs = self.provider.get_object_qs(User)

        self.assertEqual(
            set([self.users[1].pk, self.users[2].pk, self.users[4].pk]),
            set(user_qs.values_list("pk", flat=True)),
        )
