"""SCIM Group Filters tests"""

from django.test import TestCase

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application, Group, User
from authentik.lib.generators import generate_id
from authentik.providers.scim.models import SCIMMapping, SCIMProvider


class SCIMFilterGroupsTests(TestCase):
    """SCIM Group Filters tests"""

    @apply_blueprint("system/providers-scim.yaml")
    def setUp(self) -> None:
        # Delete all users and groups as to only have the test users and groups
        User.objects.all().exclude_anonymous().delete()
        Group.objects.all().delete()

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

        # Create test groups
        self.group1 = Group.objects.create(name="group-1")
        self.group2 = Group.objects.create(name="group-2")
        self.group3 = Group.objects.create(name="group-3")

    def test_no_group_filters(self):
        """Test with no group filters set"""
        group_qs = self.provider.get_object_qs(Group)

        self.assertEqual(
            set([self.group1.pk, self.group2.pk, self.group3.pk]),
            set(group_qs.values_list("pk", flat=True)),
        )

    def test_single_group_filter(self):
        """Test with one group filter set"""
        self.provider.group_filters.add(self.group1)

        group_qs = self.provider.get_object_qs(Group)

        self.assertEqual(
            set([self.group1.pk]),
            set(group_qs.values_list("pk", flat=True)),
        )

    def test_multiple_group_filters(self):
        """Test with multiple group filters set"""
        self.provider.group_filters.add(self.group1)
        self.provider.group_filters.add(self.group2)

        group_qs = self.provider.get_object_qs(Group)

        self.assertEqual(
            set([self.group1.pk, self.group2.pk]),
            set(group_qs.values_list("pk", flat=True)),
        )
