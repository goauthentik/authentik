"""Slack Type tests"""

from unittest.mock import patch

from django.test import TestCase

from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.slack import (
    SlackOAuth2Callback,
    SlackOAuthClient,
    SlackType,
)

# https://api.slack.com/methods/openid.connect.userInfo
SLACK_USER = {
    "ok": True,
    "sub": "U09VAHA70UU",
    "https://slack.com/user_id": "U09VAHA70UU",
    "https://slack.com/team_id": "T08G285D7DX",
    "email": "user@example.com",
    "email_verified": True,
    "name": "Test User",
    "picture": "https://secure.gravatar.com/avatar/test.jpg",
    "given_name": "Test",
    "family_name": "User",
    "locale": "en-US",
    "https://slack.com/team_name": "Test Workspace",
    "https://slack.com/team_domain": "test-workspace",
}

# https://api.slack.com/methods/oauth.v2.access
# Slack oauth.v2.access response with user token (Sign in with Slack, no token rotation)
SLACK_TOKEN_RESPONSE = {
    "ok": True,
    "app_id": "A0118NQPZZC",
    "authed_user": {
        "id": "U065VRX1T0",
        "scope": "openid,email,profile",
        "access_token": "xoxp-user-token-12345",
        "token_type": "user",
    },
    "team": {"id": "T024BE7LD"},
    "enterprise": None,
    "is_enterprise_install": False,
}

# https://api.slack.com/methods/oauth.v2.access
# https://api.slack.com/authentication/rotation
# Slack oauth.v2.access response with token rotation enabled
SLACK_TOKEN_RESPONSE_WITH_REFRESH = {
    "ok": True,
    "app_id": "A0KRD7HC3",
    "authed_user": {
        "id": "U1234",
        "scope": "openid,email,profile",
        "access_token": "xoxe.xoxp-1234",
        "refresh_token": "xoxe-1-refresh-token",
        "token_type": "user",
        "expires_in": 43200,
    },
    "team": {"id": "T9TK3CUKW", "name": "Slack Softball Team"},
    "enterprise": None,
    "is_enterprise_install": False,
}


class TestTypeSlack(TestCase):
    """Slack OAuth Source tests"""

    def setUp(self):
        self.source = OAuthSource.objects.create(
            name="test",
            slug="test",
            provider_type="slack",
        )

    def test_enroll_context(self):
        """Test Slack enrollment context"""
        ak_context = SlackType().get_base_user_properties(
            source=self.source, info=SLACK_USER, token={}
        )
        self.assertEqual(ak_context["username"], SLACK_USER["name"])
        self.assertEqual(ak_context["email"], SLACK_USER["email"])
        self.assertEqual(ak_context["name"], SLACK_USER["name"])

    def test_get_user_id(self):
        """Test Slack user ID extraction from profile info"""
        callback = SlackOAuth2Callback()
        # Test with 'sub' field (OIDC userinfo response)
        self.assertEqual(callback.get_user_id({"sub": "U12345"}), "U12345")
        # Test with no sub
        self.assertIsNone(callback.get_user_id({}))

    def test_token_extraction_user_token(self):
        """Test that user token is extracted from nested authed_user"""
        client = SlackOAuthClient(self.source, None)

        # Mock the parent class method to return Slack's nested response
        with patch(
            "authentik.sources.oauth.clients.oauth2.OAuth2Client.get_access_token"
        ) as mock_parent:
            mock_parent.return_value = SLACK_TOKEN_RESPONSE.copy()

            token = client.get_access_token()

            # Verify user token was extracted to top level
            self.assertEqual(token["access_token"], "xoxp-user-token-12345")
            # Verify token_type was normalized to Bearer
            self.assertEqual(token["token_type"], "Bearer")
            # Verify user ID was extracted
            self.assertEqual(token["id"], "U065VRX1T0")

    def test_token_extraction_with_refresh(self):
        """Test that refresh_token and expires_in are extracted when present"""
        client = SlackOAuthClient(self.source, None)

        with patch(
            "authentik.sources.oauth.clients.oauth2.OAuth2Client.get_access_token"
        ) as mock_parent:
            mock_parent.return_value = SLACK_TOKEN_RESPONSE_WITH_REFRESH.copy()

            token = client.get_access_token()

            # Verify tokens were extracted from authed_user
            self.assertEqual(token["access_token"], "xoxe.xoxp-1234")
            self.assertEqual(token["refresh_token"], "xoxe-1-refresh-token")
            self.assertEqual(token["expires_in"], 43200)
            self.assertEqual(token["token_type"], "Bearer")
            self.assertEqual(token["id"], "U1234")

    def test_token_type_always_bearer(self):
        """Test that token_type is always set to Bearer"""
        client = SlackOAuthClient(self.source, None)

        # Test with authed_user response
        with patch(
            "authentik.sources.oauth.clients.oauth2.OAuth2Client.get_access_token"
        ) as mock_parent:
            mock_parent.return_value = {
                "ok": True,
                "authed_user": {
                    "id": "U12345",
                    "access_token": "xoxp-test",
                    "token_type": "user",  # Slack returns "user"
                },
            }
            token = client.get_access_token()
            self.assertEqual(token["token_type"], "Bearer")

        # Test with bot token response (no authed_user)
        with patch(
            "authentik.sources.oauth.clients.oauth2.OAuth2Client.get_access_token"
        ) as mock_parent:
            mock_parent.return_value = {
                "ok": True,
                "access_token": "xoxb-bot-token",
                # No token_type in response
            }
            token = client.get_access_token()
            self.assertEqual(token["token_type"], "Bearer")

    def test_token_error_passthrough(self):
        """Test that error responses are passed through unchanged"""
        client = SlackOAuthClient(self.source, None)

        with patch(
            "authentik.sources.oauth.clients.oauth2.OAuth2Client.get_access_token"
        ) as mock_parent:
            mock_parent.return_value = {"error": "invalid_grant"}
            token = client.get_access_token()
            self.assertEqual(token, {"error": "invalid_grant"})

    def test_token_none_passthrough(self):
        """Test that None is passed through"""
        client = SlackOAuthClient(self.source, None)

        with patch(
            "authentik.sources.oauth.clients.oauth2.OAuth2Client.get_access_token"
        ) as mock_parent:
            mock_parent.return_value = None
            token = client.get_access_token()
            self.assertIsNone(token)
