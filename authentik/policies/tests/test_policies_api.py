"""Test policies API"""

from json import loads
from unittest.mock import MagicMock, patch

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user
from authentik.policies.dummy.models import DummyPolicy
from authentik.policies.types import PolicyResult


class TestPoliciesAPI(APITestCase):
    """Test policies API"""

    def setUp(self) -> None:
        super().setUp()
        self.policy = DummyPolicy.objects.create(name="dummy", result=True)
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    @patch("authentik.policies.dummy.models.DummyPolicy.passes")
    def test_test_call(self, passes_mock: MagicMock):
        """Test Policy's test endpoint"""
        passes_mock.return_value = PolicyResult(True, "dummy")
        response = self.client.post(
            reverse("authentik_api:policy-test", kwargs={"pk": self.policy.pk}),
            data={
                "user": self.user.pk,
            },
        )
        body = loads(response.content.decode())
        self.assertEqual(body["passing"], True)
        self.assertEqual(body["messages"], ["dummy"])
        self.assertEqual(body["log_messages"], [])

    def test_test_call_invalid(self):
        """Test invalid policy test"""
        response = self.client.post(
            reverse("authentik_api:policy-test", kwargs={"pk": self.policy.pk}),
            data={},
        )
        self.assertEqual(response.status_code, 400)
        response = self.client.post(
            reverse("authentik_api:policy-test", kwargs={"pk": self.policy.pk}),
            data={
                "user": self.user.pk + 1,
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_types(self):
        """Test Policy's types endpoint"""
        response = self.client.get(
            reverse("authentik_api:policy-types"),
        )
        self.assertEqual(response.status_code, 200)

    def test_sort_by_last_updated(self):
        """Test API sorting by last_updated"""
        other = DummyPolicy.objects.create(name="dummy-other", result=True)
        # Re-save the policy created in setUp so it becomes the most recently updated one
        self.policy.save()

        def ordered_pks(ordering: str) -> list[str]:
            response = self.client.get(
                reverse("authentik_api:policy-list"),
                data={
                    "ordering": ordering,
                    "page_size": 100,
                },
            )
            self.assertEqual(response.status_code, 200)
            return [policy["pk"] for policy in loads(response.content.decode())["results"]]

        descending = ordered_pks("-last_updated")
        self.assertLess(descending.index(str(self.policy.pk)), descending.index(str(other.pk)))

        ascending = ordered_pks("last_updated")
        self.assertLess(ascending.index(str(other.pk)), ascending.index(str(self.policy.pk)))

    def test_cache_info(self):
        """Test Policy's cache_info endpoint"""
        response = self.client.get(
            reverse("authentik_api:policy-cache-info"),
        )
        self.assertEqual(response.status_code, 200)

    def test_cache_clear(self):
        """Test Policy's cache_clear endpoint"""
        response = self.client.post(
            reverse("authentik_api:policy-cache-clear"),
        )
        self.assertEqual(response.status_code, 204)
