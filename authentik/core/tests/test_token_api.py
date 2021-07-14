"""Test token API"""
from django.urls.base import reverse
from rest_framework.test import APITestCase

from authentik.core.models import (
    USER_ATTRIBUTE_TOKEN_EXPIRING,
    Token,
    TokenIntents,
    User,
)


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
        token = Token.objects.get(identifier="test-token")
        self.assertEqual(token.user, self.user)
        self.assertEqual(token.intent, TokenIntents.INTENT_API)
        self.assertEqual(token.expiring, True)

    def test_token_create_non_expiring(self):
        """Test token creation endpoint"""
        self.user.attributes[USER_ATTRIBUTE_TOKEN_EXPIRING] = False
        self.user.save()
        response = self.client.post(
            reverse("authentik_api:token-list"), {"identifier": "test-token"}
        )
        self.assertEqual(response.status_code, 201)
        token = Token.objects.get(identifier="test-token")
        self.assertEqual(token.user, self.user)
        self.assertEqual(token.intent, TokenIntents.INTENT_API)
        self.assertEqual(token.expiring, False)
