"""SCIM Application Policies tests"""

from unittest.mock import patch

from django.test import TestCase

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application, Group, User
from authentik.lib.generators import generate_id
from authentik.lib.sync.outgoing.signals import sync_outgoing_inhibit_dispatch
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

        self.users[1].groups.add(self.group1)
        self.users[2].groups.add(self.group2)
        self.users[4].groups.add(self.group1)
        self.users[4].groups.add(self.group2)

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

    def test_group_policy_member_add_dispatches_sync(self):
        """Adding a user to a policy-bound group triggers a full SCIM sync"""
        PolicyBinding.objects.create(target=self.app, group=self.group1, order=0)

        with patch("authentik.providers.scim.signals.scim_sync.send_with_options") as sync:
            self.users[3].groups.add(self.group1)

        sync.assert_called_once()
        self.assertEqual(sync.call_args.kwargs["args"], (self.provider.pk,))

    def test_group_policy_member_remove_dispatches_sync(self):
        """Removing a user from a policy-bound group triggers SCIM cleanup"""
        PolicyBinding.objects.create(target=self.app, group=self.group1, order=0)

        with patch("authentik.providers.scim.signals.scim_sync.send_with_options") as sync:
            self.group1.users.remove(self.users[1])

        sync.assert_called_once()
        self.assertEqual(sync.call_args.kwargs["args"], (self.provider.pk,))

    def test_unbound_group_member_change_does_not_dispatch_sync(self):
        """Changing a group outside application policy bindings does not sync"""
        PolicyBinding.objects.create(target=self.app, group=self.group1, order=0)

        with patch("authentik.providers.scim.signals.scim_sync.send_with_options") as sync:
            self.users[3].groups.add(self.group3)

        sync.assert_not_called()

    def test_inhibited_member_change_does_not_dispatch_sync(self):
        """Bulk sync contexts can inhibit application-policy sync dispatch"""
        PolicyBinding.objects.create(target=self.app, group=self.group1, order=0)

        with (
            sync_outgoing_inhibit_dispatch(),
            patch("authentik.providers.scim.signals.scim_sync.send_with_options") as sync,
        ):
            self.users[3].groups.add(self.group1)

        sync.assert_not_called()
