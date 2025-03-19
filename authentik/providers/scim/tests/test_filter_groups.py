"""SCIM Filter Groups tests"""

from django.test import TestCase
from requests_mock import Mocker

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application, Group, User
from authentik.lib.generators import generate_id
from authentik.providers.scim.models import SCIMMapping, SCIMProvider
from authentik.providers.scim.tasks import scim_sync, sync_tasks


class SCIMFilterGroupsTests(TestCase):
    """SCIM Filter Groups tests"""

    @apply_blueprint("system/providers-scim.yaml")
    def setUp(self) -> None:
        # Set up SCIM Provider
        self.provider: SCIMProvider = SCIMProvider.objects.create(
            name=generate_id(),
            url="https://localhost",
            token=generate_id(),
            exclude_users_service_account=True,
        )

        self.app: Application = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        self.app.backchannel_providers.add(self.provider)
        self.provider.property_mappings.add(
            SCIMMapping.objects.get(managed="goauthentik.io/providers/scim/user")
        )
        self.provider.property_mappings_group.add(
            SCIMMapping.objects.get(managed="goauthentik.io/providers/scim/group")
        )

        # Create test groups
        self.filter_group1 = Group.objects.create(name="filter-group-1")
        self.filter_group2 = Group.objects.create(name="filter-group-2")
        self.unfiltered_group = Group.objects.create(name="unfiltered-group")

        # Define group lists for testing
        self.filter_groups = [self.filter_group1, self.filter_group2]
        self.non_filter_groups = [self.unfiltered_group]
        self.all_groups = self.filter_groups + self.non_filter_groups

        # Create users in a loop and store in a dictionary
        self.users = {}
        for i in range(1, 5):
            uid = generate_id()
            self.users[i] = User.objects.create(
                username=uid,
                name=f"{uid} User",
                email=f"{uid}@goauthentik.io",
            )

        # Define user groups
        self.users_in_group1 = [self.users[1], self.users[3]]
        self.users_in_group2 = [self.users[2], self.users[3]]
        self.users_in_unfiltered_group = [self.users[4]]

        # Calculate remaining groups
        self.users_in_any_filter_group = list(set(self.users_in_group1 + self.users_in_group2))
        self.all_users = list(self.users.values())
        self.users_not_in_filter_groups = [
            user for user in self.users.values()
            if user not in self.users_in_any_filter_group
        ]

        # Assign users to groups
        for user in self.users.values():
            if user in self.users_in_group1:
                user.ak_groups.add(self.filter_group1)
            if user in self.users_in_group2:
                user.ak_groups.add(self.filter_group2)
            if user in self.users_in_unfiltered_group:
                user.ak_groups.add(self.unfiltered_group)

    def test_no_filter_groups(self):
        """Test with no filter groups set"""
        # No filter groups set, should include all users and groups
        users = self.provider.get_object_qs(User)
        groups = self.provider.get_object_qs(Group)

        self.assertEqual(users.count(), len(self.all_users))
        self.assertGreaterEqual(groups.count(), len(self.all_groups))

        # Verify all users are included
        user_pks = list(users.values_list('pk', flat=True))
        for user in self.all_users:
            self.assertIn(user.pk, user_pks)

        # Verify all test groups are included
        group_pks = list(groups.values_list('pk', flat=True))
        for group in self.all_groups:
            self.assertIn(group.pk, group_pks)

    def test_single_filter_group(self):
        """Test with one filter group set"""
        # Set single filter group
        self.provider.filter_groups.add(self.filter_group1)

        users = self.provider.get_object_qs(User)
        groups = self.provider.get_object_qs(Group)

        # Verify test group is included
        self.assertEqual(groups.count(), 1)

        # Verify only users in filter_group1 are included
        user_pks = set(users.values_list('pk', flat=True))
        for user in self.all_users:
            if(user in self.users_in_group1):
                self.assertIn(user.pk, user_pks)
            else:
                self.assertNotIn(user.pk, user_pks)

        # Verify only filter_group1 is included
        group_pks = list(groups.values_list('pk', flat=True))
        for group in self.all_groups:
            if(group == self.filter_group1):
                self.assertIn(group.pk, group_pks)
            else:
                self.assertNotIn(group.pk, group_pks)

    def test_multiple_filter_groups(self):
        """Test with multiple filter groups set"""
        # Set multiple filter groups
        self.provider.filter_groups.add(*self.filter_groups)

        users = self.provider.get_object_qs(User)
        groups = self.provider.get_object_qs(Group)

        # Only the two filter groups should be included
        self.assertEqual(groups.count(), len(self.filter_groups))

        # Verify users in either filter_group1 or filter_group2 are included
        user_pks = set(users.values_list('pk', flat=True))
        for user in self.all_users:
            if(user in self.users_in_any_filter_group):
                self.assertIn(user.pk, user_pks)
            else:
                self.assertNotIn(user.pk, user_pks)

        # Verify only the filter groups are included
        group_pks = list(groups.values_list('pk', flat=True))
        for group in self.all_groups:
            if(group in self.filter_groups):
                self.assertIn(group.pk, group_pks)
            else:
                self.assertNotIn(group.pk, group_pks)

    @Mocker()
    def test_sync_with_filter_groups(self, mock: Mocker):
        """Test synchronization with filter groups set"""
        # Add filter groups
        self.provider.filter_groups.add(*self.filter_groups)

        # Set up mock responses
        mock.get(
            "https://localhost/ServiceProviderConfig",
            json={},
        )

        # Mock user creation
        expected_users = self.users_in_any_filter_group
        for user in expected_users:
            # Mock POST response for creating the user
            mock.post(
                "https://localhost/Users",
                json={"id": str(user.uid)},
            )
            # Mock PUT response for updating the user
            mock.put(
                f"https://localhost/Users/{user.uid}",
                json={"id": str(user.uid)},
            )
            # Mock PATCH response for patching the user
            mock.patch(
                f"https://localhost/Users/{user.uid}",
                json={"id": str(user.uid)},
            )

        # Mock group creation
        expected_groups = self.filter_groups
        for group in expected_groups:
            # Mock POST response for creating the group
            mock.post(
                "https://localhost/Groups",
                json={"id": str(group.pk)},
            )
            # Mock PUT response for updating the group
            mock.put(
                f"https://localhost/Groups/{group.pk}",
                json={"id": str(group.pk)},
            )
            # Mock PATCH response for patching the group
            mock.patch(
                f"https://localhost/Groups/{group.pk}",
                json={"id": str(group.pk)},
            )

        # Execute sync
        sync_tasks.trigger_single_task(self.provider, scim_sync).get()

        # Count POST calls to different endpoints
        user_posts = 0
        group_posts = 0
        for req in mock.request_history:
            if req.method == "POST":
                if req.url == "https://localhost/Users":
                    user_posts += 1
                elif req.url == "https://localhost/Groups":
                    group_posts += 1

        # Verify number of synchronized users
        self.assertEqual(user_posts, len(self.users_in_any_filter_group), f"Expected {len(self.users_in_any_filter_group)} users to be synchronized")
        # Verify number of synchronized groups
        self.assertEqual(group_posts, len(self.filter_groups), f"Expected {len(self.users_in_any_filter_group)} groups to be synchronized")
