"""Test policies API"""
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import User
from authentik.policies.dummy.models import DummyPolicy


class TestPoliciesAPI(APITestCase):
    """Test policies API"""

    def setUp(self) -> None:
        super().setUp()
        self.policy = DummyPolicy.objects.create(name="dummy", result=True)
        self.user = User.objects.get(username="akadmin")
        self.client.force_login(self.user)

    def test_test_call(self):
        """Test Policy's test endpoint"""
        response = self.client.post(
            reverse("authentik_api:policy-test", kwargs={"pk": self.policy.pk}),
            data={
                "user": self.user.pk,
            },
        )
        self.assertJSONEqual(response.content.decode(), {"passing": True, "messages": ["dummy"]})

    def test_types(self):
        """Test Policy's types endpoint"""
        response = self.client.get(
            reverse("authentik_api:policy-types"),
        )
        self.assertEqual(response.status_code, 200)
