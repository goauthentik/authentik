"""Test API Authentication"""
from base64 import b64encode

from django.test import TestCase
from guardian.shortcuts import get_anonymous_user

from authentik.api.auth import token_from_header
from authentik.core.models import Token, TokenIntents


class TestAPIAuth(TestCase):
    """Test API Authentication"""

    def test_valid(self):
        """Test valid token"""
        token = Token.objects.create(
            intent=TokenIntents.INTENT_API, user=get_anonymous_user()
        )
        auth = b64encode(f":{token.key}".encode()).decode()
        self.assertEqual(token_from_header(f"Basic {auth}".encode()), token)

    def test_invalid_type(self):
        """Test invalid type"""
        self.assertIsNone(token_from_header("foo bar".encode()))

    def test_invalid_decode(self):
        """Test invalid bas64"""
        self.assertIsNone(token_from_header("Basic bar".encode()))

    def test_invalid_empty_password(self):
        """Test invalid with empty password"""
        self.assertIsNone(token_from_header("Basic :".encode()))

    def test_invalid_no_token(self):
        """Test invalid with no token"""
        auth = b64encode(":abc".encode()).decode()
        self.assertIsNone(token_from_header(f"Basic :{auth}".encode()))
