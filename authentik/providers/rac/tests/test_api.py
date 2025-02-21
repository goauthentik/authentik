"""Test RAC Provider"""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.lib.generators import generate_id


class TestAPI(APITestCase):
    """Test Provider API"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()

    def test_create(self):
        """Test creation of RAC Provider"""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("authentik_api:racprovider-list"),
            data={
                "name": generate_id(),
                "authorization_flow": create_test_flow().pk,
            },
        )
        self.assertEqual(response.status_code, 201)
