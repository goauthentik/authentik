"""User count API tests."""

from datetime import timedelta

from django.urls import reverse
from django.utils.timezone import now
from rest_framework.test import APITestCase

from authentik.core.models import User, UserTypes
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.enterprise.license import LicenseKey


class TestUserCountsAPI(APITestCase):
    """Test relative and absolute user count ranges."""

    def setUp(self):
        self.admin = create_test_admin_user()
        self.client.force_login(self.admin)
        User.objects.filter(type__in=(UserTypes.INTERNAL, UserTypes.EXTERNAL)).update(
            date_joined=now() - timedelta(days=400)
        )
        self.internal_users = LicenseKey.get_internal_user_count()
        self.external_users = LicenseKey.get_external_user_count()

    def create_user(self, user_type: UserTypes, age_days: int, *, is_active: bool = True) -> User:
        """Create a user with a specific account age."""
        user = create_test_user(type=user_type, is_active=is_active)
        User.objects.filter(pk=user.pk).update(date_joined=now() - timedelta(days=age_days))
        return user

    def test_user_counts_relative_ranges(self):
        """Relative ranges count active users by date_joined."""
        for user_type in (UserTypes.INTERNAL, UserTypes.EXTERNAL):
            self.create_user(user_type, 15)
            self.create_user(user_type, 60)
            self.create_user(user_type, 180)
            self.create_user(user_type, 400)
            self.create_user(user_type, 15, is_active=False)

        response = self.client.get(
            reverse("authentik_api:license-user-counts"),
            {"count_steps": ["days=30", "days=90", "days=365"]},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["active_internal_users"], self.internal_users + 4)
        self.assertEqual(response.data["active_external_users"], self.external_users + 4)
        ranges = {item["interval"]: item for item in response.data["ranges"]}
        self.assertEqual(
            {
                interval: (
                    ranges[interval]["internal_users_added"],
                    ranges[interval]["external_users_added"],
                )
                for interval in ("days=30", "days=90", "days=365")
            },
            {
                "days=30": (1, 1),
                "days=90": (2, 2),
                "days=365": (3, 3),
            },
        )

    def test_user_counts_custom_ranges(self):
        """Relative and absolute ranges can be requested together."""
        self.create_user(UserTypes.INTERNAL, 60)
        self.create_user(UserTypes.EXTERNAL, 60)
        response = self.client.get(
            reverse("authentik_api:license-user-counts"),
            {
                "count_steps": ["days=70"],
                "start": (now() - timedelta(days=70)).isoformat(),
                "end": (now() - timedelta(days=50)).isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["ranges"]), 2)
        self.assertEqual(response.data["ranges"][0]["interval"], "days=70")
        self.assertEqual(response.data["ranges"][0]["internal_users_added"], 1)
        self.assertEqual(response.data["ranges"][0]["external_users_added"], 1)
        self.assertIsNone(response.data["ranges"][1]["interval"])
        self.assertEqual(response.data["ranges"][1]["internal_users_added"], 1)
        self.assertEqual(response.data["ranges"][1]["external_users_added"], 1)

    def test_user_counts_invalid_ranges(self):
        """Invalid relative and absolute ranges are rejected."""
        url = reverse("authentik_api:license-user-counts")
        for query in (
            {},
            {"count_steps": ["days=0"]},
            {"start": now().isoformat()},
            {
                "start": now().isoformat(),
                "end": (now() - timedelta(days=1)).isoformat(),
            },
        ):
            with self.subTest(query=query):
                self.assertEqual(self.client.get(url, query).status_code, 400)
