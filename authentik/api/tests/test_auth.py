"""Test API Authentication"""
from base64 import b64encode

from django.conf import settings
from django.test import TestCase
from guardian.shortcuts import get_anonymous_user
from rest_framework.exceptions import AuthenticationFailed

from authentik.api.authentication import bearer_auth
from authentik.blueprints.tests import reconcile_app
from authentik.core.models import USER_ATTRIBUTE_SA, Token, TokenIntents
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.constants import SCOPE_AUTHENTIK_API
from authentik.providers.oauth2.models import OAuth2Provider, RefreshToken


class TestAPIAuth(TestCase):
    """Test API Authentication"""

    def test_invalid_type(self):
        """Test invalid type"""
        with self.assertRaises(AuthenticationFailed):
            bearer_auth("foo bar".encode())

    def test_invalid_empty(self):
        """Test invalid type"""
        self.assertIsNone(bearer_auth("Bearer ".encode()))
        self.assertIsNone(bearer_auth("".encode()))

    def test_invalid_no_token(self):
        """Test invalid with no token"""
        with self.assertRaises(AuthenticationFailed):
            auth = b64encode(":abc".encode()).decode()
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

    def test_managed_outpost(self):
        """Test managed outpost"""
        with self.assertRaises(AuthenticationFailed):
            bearer_auth(f"Bearer {settings.SECRET_KEY}".encode())

    @reconcile_app("authentik_outposts")
    def test_managed_outpost_success(self):
        """Test managed outpost"""
        user = bearer_auth(f"Bearer {settings.SECRET_KEY}".encode())
        self.assertEqual(user.attributes[USER_ATTRIBUTE_SA], True)

    def test_jwt_valid(self):
        """Test valid JWT"""
        provider = OAuth2Provider.objects.create(
            name=generate_id(), client_id=generate_id(), authorization_flow=create_test_flow()
        )
        refresh = RefreshToken.objects.create(
            user=create_test_admin_user(),
            provider=provider,
            refresh_token=generate_id(),
            _scope=SCOPE_AUTHENTIK_API,
        )
        self.assertEqual(bearer_auth(f"Bearer {refresh.refresh_token}".encode()), refresh.user)

    def test_jwt_missing_scope(self):
        """Test valid JWT"""
        provider = OAuth2Provider.objects.create(
            name=generate_id(), client_id=generate_id(), authorization_flow=create_test_flow()
        )
        refresh = RefreshToken.objects.create(
            user=create_test_admin_user(),
            provider=provider,
            refresh_token=generate_id(),
            _scope="",
        )
        with self.assertRaises(AuthenticationFailed):
            self.assertEqual(bearer_auth(f"Bearer {refresh.refresh_token}".encode()), refresh.user)
