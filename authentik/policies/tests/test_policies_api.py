"""Test policies API"""

from json import loads
from unittest.mock import MagicMock, patch

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.lib.generators import generate_id
from authentik.policies.dummy.models import DummyPolicy
from authentik.policies.expression.models import ExpressionPolicy
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

    def test_test_call_subclass_object_perms(self):
        """Test Policy's test endpoint with object permissions on the subclass only"""
        policy = ExpressionPolicy.objects.create(name=generate_id(), expression="return True")
        user = create_test_user()
        user.assign_perms_to_managed_role("authentik_core.view_user", user)
        user.assign_perms_to_managed_role(
            [
                "authentik_policies_expression.view_expressionpolicy",
                "authentik_policies_expression.add_expressionpolicy",
            ],
            policy,
        )
        self.client.force_login(user)
        response = self.client.post(
            reverse("authentik_api:policy-test", kwargs={"pk": policy.pk}),
            data={"user": user.pk},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(loads(response.content.decode())["passing"])

    def test_test_call_subclass_denied(self):
        """Test Policy's test endpoint without permissions"""
        policy = ExpressionPolicy.objects.create(name=generate_id(), expression="return True")
        user = create_test_user()
        user.assign_perms_to_managed_role("authentik_core.view_user", user)
        self.client.force_login(user)
        url = reverse("authentik_api:policy-test", kwargs={"pk": policy.pk})
        response = self.client.post(url, data={"user": user.pk})
        self.assertEqual(response.status_code, 403)
        # Passes the POST object permission check, but not the action's view permission
        user.assign_perms_to_managed_role(
            "authentik_policies_expression.add_expressionpolicy", policy
        )
        response = self.client.post(url, data={"user": user.pk})
        self.assertEqual(response.status_code, 403)

    def test_destroy_subclass_object_perms(self):
        """Test deleting a policy through the base viewset with object permissions
        on the subclass"""
        policy = ExpressionPolicy.objects.create(name=generate_id(), expression="return True")
        user = create_test_user()
        user.assign_perms_to_managed_role("authentik_policies.view_policy")
        self.client.force_login(user)
        response = self.client.delete(
            reverse("authentik_api:policy-detail", kwargs={"pk": policy.pk}),
        )
        self.assertEqual(response.status_code, 403)
        user.assign_perms_to_managed_role(
            "authentik_policies_expression.delete_expressionpolicy", policy
        )
        response = self.client.delete(
            reverse("authentik_api:policy-detail", kwargs={"pk": policy.pk}),
        )
        self.assertEqual(response.status_code, 204)
        self.assertFalse(ExpressionPolicy.objects.filter(pk=policy.pk).exists())
