"""Test API Authentication"""
from base64 import b64encode

from django.test import TestCase
from guardian.shortcuts import get_anonymous_user
from rest_framework.exceptions import AuthenticationFailed

from authentik.api.auth import token_from_header
from authentik.core.models import Token, TokenIntents


class TestAPIAuth(TestCase):
    """Test API Authentication"""

    def test_valid_basic(self):
        """Test valid token"""
        token = Token.objects.create(
            intent=TokenIntents.INTENT_API, user=get_anonymous_user()
        )
        auth = b64encode(f":{token.key}".encode()).decode()
        self.assertEqual(token_from_header(f"Basic {auth}".encode()), token)

    def test_valid_bearer(self):
        """Test valid token"""
        token = Token.objects.create(
            intent=TokenIntents.INTENT_API, user=get_anonymous_user()
        )
        self.assertEqual(token_from_header(f"Bearer {token.key}".encode()), token)

    def test_invalid_type(self):
        """Test invalid type"""
        with self.assertRaises(AuthenticationFailed):
            token_from_header("foo bar".encode())

    def test_invalid_decode(self):
        """Test invalid bas64"""
        with self.assertRaises(AuthenticationFailed):
            token_from_header("Basic bar".encode())

    def test_invalid_empty_password(self):
        """Test invalid with empty password"""
        with self.assertRaises(AuthenticationFailed):
            token_from_header("Basic :".encode())

    def test_invalid_no_token(self):
        """Test invalid with no token"""
        with self.assertRaises(AuthenticationFailed):
            auth = b64encode(":abc".encode()).decode()
            self.assertIsNone(token_from_header(f"Basic :{auth}".encode()))
