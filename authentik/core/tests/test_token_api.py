"""Test token API"""
from django.urls.base import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Token, User


class TestTokenAPI(APITestCase):
    """Test token API"""

    def setUp(self) -> None:
        super().setUp()
        self.user = User.objects.get(username="akadmin")
        self.client.force_login(self.user)

    def test_token_create(self):
        """Test token creation endpoint"""
        response = self.client.post(
            reverse("authentik_api:token-list"), {"identifier": "test-token"}
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Token.objects.get(identifier="test-token").user, self.user)
