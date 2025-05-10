"""Test token auth"""

from django.test import TestCase

from authentik.common.tests import get_request
from authentik.core.auth import TokenBackend
from authentik.core.models import Token, TokenIntents, User
from authentik.flows.planner import FlowPlan
from authentik.flows.views.executor import SESSION_KEY_PLAN


class TestTokenAuth(TestCase):
    """Test token auth"""

    def setUp(self) -> None:
        self.user = User.objects.create(username="test-user")
        self.token = Token.objects.create(
            expiring=False, user=self.user, intent=TokenIntents.INTENT_APP_PASSWORD
        )
        # To test with session we need to create a request and pass it through all middlewares
        self.request = get_request("/")
        self.request.session[SESSION_KEY_PLAN] = FlowPlan("test")

    def test_token_auth(self):
        """Test auth with token"""
        self.assertEqual(
            TokenBackend().authenticate(self.request, "test-user", self.token.key), self.user
        )

    def test_token_auth_none(self):
        """Test auth with token (non-existent user)"""
        self.assertIsNone(
            TokenBackend().authenticate(self.request, "test-user-foo", self.token.key), self.user
        )

    def test_token_auth_invalid(self):
        """Test auth with token (invalid token)"""
        self.assertIsNone(
            TokenBackend().authenticate(self.request, "test-user", self.token.key + "foo"),
            self.user,
        )
