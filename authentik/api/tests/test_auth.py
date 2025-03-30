"""Test API Authentication"""

import json
from base64 import b64encode

from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed

from authentik.api.authentication import bearer_auth
from authentik.common.oauth.constants import SCOPE_AUTHENTIK_API
from authentik.core.models import Token, TokenIntents
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import AccessToken, OAuth2Provider


class TestAPIAuth(TestCase):
    """Test API Authentication"""

    def test_invalid_type(self):
        """Test invalid type"""
        with self.assertRaises(AuthenticationFailed):
            bearer_auth(b"foo bar")

    def test_invalid_empty(self):
        """Test invalid type"""
        self.assertIsNone(bearer_auth(b"Bearer "))
        self.assertIsNone(bearer_auth(b""))

    def test_invalid_no_token(self):
        """Test invalid with no token"""
        with self.assertRaises(AuthenticationFailed):
            auth = b64encode(b":abc").decode()
            self.assertIsNone(bearer_auth(f"Basic :{auth}".encode()))

    def test_bearer_valid(self):
        """Test valid token"""
        token = Token.objects.create(intent=TokenIntents.INTENT_API, user=create_test_admin_user())
        self.assertEqual(bearer_auth(f"Bearer {token.key}".encode()), token.user)

    def test_bearer_valid_deactivated(self):
        """Test valid token"""
        user = create_test_admin_user()
        user.is_active = False
        user.save()
        token = Token.objects.create(intent=TokenIntents.INTENT_API, user=user)
        with self.assertRaises(AuthenticationFailed):
            bearer_auth(f"Bearer {token.key}".encode())

    def test_jwt_valid(self):
        """Test valid JWT"""
        provider = OAuth2Provider.objects.create(
            name=generate_id(), client_id=generate_id(), authorization_flow=create_test_flow()
        )
        refresh = AccessToken.objects.create(
            user=create_test_admin_user(),
            provider=provider,
            token=generate_id(),
            auth_time=timezone.now(),
            _scope=SCOPE_AUTHENTIK_API,
            _id_token=json.dumps({}),
        )
        self.assertEqual(bearer_auth(f"Bearer {refresh.token}".encode()), refresh.user)

    def test_jwt_missing_scope(self):
        """Test valid JWT"""
        provider = OAuth2Provider.objects.create(
            name=generate_id(), client_id=generate_id(), authorization_flow=create_test_flow()
        )
        refresh = AccessToken.objects.create(
            user=create_test_admin_user(),
            provider=provider,
            token=generate_id(),
            auth_time=timezone.now(),
            _scope="",
            _id_token=json.dumps({}),
        )
        with self.assertRaises(AuthenticationFailed):
            self.assertEqual(bearer_auth(f"Bearer {refresh.token}".encode()), refresh.user)
