"""Test bindings API"""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user
from authentik.policies.models import PolicyBindingModel


class TestBindingsAPI(APITestCase):
    """Test bindings API"""

    def setUp(self) -> None:
        super().setUp()
        self.pbm = PolicyBindingModel.objects.create()
        self.user = create_test_admin_user()
        self.group = self.user.ak_groups.first()
        self.client.force_login(self.user)

    def test_valid_binding(self):
        """Test valid binding"""
        response = self.client.post(
            reverse("authentik_api:policybinding-list"),
            data={"target": self.pbm.pk, "user": self.user.pk, "order": 0},
        )
        self.assertEqual(response.status_code, 201)

    def test_invalid_too_much(self):
        """Test invalid binding (too much)"""
        response = self.client.post(
            reverse("authentik_api:policybinding-list"),
            data={
                "target": self.pbm.pk,
                "user": self.user.pk,
                "group": self.group.pk,
                "order": 0,
            },
        )
        self.assertJSONEqual(
            response.content.decode(),
            {"non_field_errors": ["Only one of 'group', 'policy', 'user' can be set."]},
        )

    def test_invalid_too_little(self):
        """Test invvalid binding (too little)"""
        response = self.client.post(
            reverse("authentik_api:policybinding-list"),
            data={"target": self.pbm.pk, "order": 0},
        )
        self.assertJSONEqual(
            response.content.decode(),
            {"non_field_errors": ["One of 'group', 'policy', 'user' must be set."]},
        )
