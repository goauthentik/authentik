"""Test API Authentication"""
from base64 import b64encode

from django.conf import settings
from django.test import TestCase
from guardian.shortcuts import get_anonymous_user
from rest_framework.exceptions import AuthenticationFailed

from authentik.api.authentication import bearer_auth
from authentik.core.models import USER_ATTRIBUTE_SA, Token, TokenIntents
from authentik.outposts.managed import OutpostManager


class TestAPIAuth(TestCase):
    """Test API Authentication"""

    def test_valid_bearer(self):
        """Test valid token"""
        token = Token.objects.create(intent=TokenIntents.INTENT_API, user=get_anonymous_user())
        self.assertEqual(bearer_auth(f"Bearer {token.key}".encode()), token.user)

    def test_invalid_type(self):
        """Test invalid type"""
        with self.assertRaises(AuthenticationFailed):
            bearer_auth("foo bar".encode())

    def test_invalid_no_token(self):
        """Test invalid with no token"""
        with self.assertRaises(AuthenticationFailed):
            auth = b64encode(":abc".encode()).decode()
            self.assertIsNone(bearer_auth(f"Basic :{auth}".encode()))

    def test_managed_outpost(self):
        """Test managed outpost"""
        with self.assertRaises(AuthenticationFailed):
            user = bearer_auth(f"Bearer {settings.SECRET_KEY}".encode())

        OutpostManager().run()
        user = bearer_auth(f"Bearer {settings.SECRET_KEY}".encode())
        self.assertEqual(user.attributes[USER_ATTRIBUTE_SA], True)
