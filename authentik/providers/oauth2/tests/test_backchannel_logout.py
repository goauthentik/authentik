"""Test OAuth2 Back-Channel Logout implementation"""

import uuid
from time import time
from unittest.mock import Mock, patch

import jwt
from django.test import RequestFactory
from django.utils import timezone
from requests import Response

from authentik.core.models import Application, AuthenticatedSession, Session
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.events.models import Event
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import (
    AccessToken,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    RefreshToken,
)
from authentik.providers.oauth2.tasks import (
    send_backchannel_logout_notification,
    send_backchannel_logout_request,
)
from authentik.providers.oauth2.tests.utils import OAuthTestCase


class TestBackChannelLogout(OAuthTestCase):
    """Test Back-Channel Logout functionality"""

    def setUp(self) -> None:
        super().setUp()
        self.factory = RequestFactory()
        self.user = create_test_admin_user()
        self.app = Application.objects.create(name=generate_id(), slug="test-app")
        self.provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            redirect_uris=[
                RedirectURI(RedirectURIMatchingMode.STRICT, "http://testserver/callback"),
            ],
            signing_key=self.keypair,
        )
        self.app.provider = self.provider
        self.app.save()

    def _create_session(self, session_key=None):
        """Create a session with the given key or a generated one"""
        session_key = session_key or f"session-{generate_id()}"
        session = Session.objects.create(
            session_key=session_key,
            expires=timezone.now() + timezone.timedelta(hours=1),
            last_ip="255.255.255.255",
        )
        auth_session = AuthenticatedSession.objects.create(
            session=session,
            user=self.user,
        )
        return auth_session

    def _create_token(
        self, provider, user, session=None, token_type="access", token_id=None
    ):  # nosec
        """Create a token of the specified type"""
        token_id = token_id or f"{token_type}-token-{generate_id()}"
        kwargs = {
            "provider": provider,
            "user": user,
            "session": session,
            "token": token_id,
            "_id_token": "{}",
            "auth_time": timezone.now(),
        }

        if token_type == "access":  # nosec
            return AccessToken.objects.create(**kwargs)
        else:  # refresh
            return RefreshToken.objects.create(**kwargs)

    def _create_provider(self, name=None):
        """Create an OAuth2 provider"""
        name = name or f"provider-{generate_id()}"
        provider = OAuth2Provider.objects.create(
            name=name,
            authorization_flow=create_test_flow(),
            redirect_uris=[
                RedirectURI(RedirectURIMatchingMode.STRICT, f"http://{name}/callback"),
            ],
            signing_key=self.keypair,
        )
        return provider

    def _create_logout_token(self, provider=None, session_id=None, sub=None):
        """Create a logout token with the given parameters"""
        provider = provider or self.provider

        # Create a token with the same issuer that the view will expect
        # Use the same request object that will be used in the test
        request = self.factory.post("/backchannel_logout")

        # Create the logout token payload
        payload = {
            "iss": provider.get_issuer(request),
            "aud": provider.client_id,
            "iat": int(time()),
            "jti": str(uuid.uuid4()),
            "events": {
                "http://schemas.openid.net/event/backchannel-logout": {},
            },
        }

        # Add either sub or sid (or both)
        if sub:
            payload["sub"] = sub
        if session_id:
            payload["sid"] = session_id

        # Encode the token
        return provider.encode(payload)

    def _decode_token(self, token, provider=None):
        """Helper to decode and validate a JWT token"""
        provider = provider or self.provider
        key, alg = provider.jwt_key
        if alg != "HS256":
            key = provider.signing_key.public_key
        return jwt.decode(
            token, key, algorithms=[alg], options={"verify_exp": False, "verify_aud": False}
        )

    def test_create_logout_token_variants(self):
        """Test creating logout tokens with different combinations of parameters"""
        # Test case 1: With session_id only
        session_id = "test-session-123"
        token1 = self._create_logout_token(session_id=session_id)
        decoded1 = self._decode_token(token1)

        self.assertIn("iss", decoded1)
        self.assertEqual(decoded1["aud"], self.provider.client_id)
        self.assertIn("iat", decoded1)
        self.assertIn("jti", decoded1)
        self.assertEqual(decoded1["sid"], session_id)
        self.assertIn("events", decoded1)
        self.assertIn("http://schemas.openid.net/event/backchannel-logout", decoded1["events"])
        self.assertNotIn("sub", decoded1)

        # Test case 2: With sub only
        sub = "user-123"
        token2 = self._create_logout_token(sub=sub)
        decoded2 = self._decode_token(token2)

        self.assertEqual(decoded2["sub"], sub)
        self.assertIn("events", decoded2)
        self.assertIn("http://schemas.openid.net/event/backchannel-logout", decoded2["events"])
        self.assertNotIn("sid", decoded2)

        # Test case 3: With both session_id and sub
        token3 = self._create_logout_token(session_id=session_id, sub=sub)
        decoded3 = self._decode_token(token3)

        self.assertEqual(decoded3["sid"], session_id)
        self.assertEqual(decoded3["sub"], sub)
        self.assertIn("events", decoded3)

    @patch("authentik.providers.oauth2.tasks.get_http_session")
    def test_send_backchannel_logout_request_scenarios(self, mock_get_session):
        """Test various scenarios for backchannel logout request task"""
        # Setup provider with backchannel logout URI
        self.provider.backchannel_logout_uris = [
            RedirectURI(RedirectURIMatchingMode.STRICT, "http://testserver/backchannel_logout")
        ]
        self.provider.save()

        # Setup mock session and response
        mock_session = Mock()
        mock_get_session.return_value = mock_session
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None  # No exception for successful request
        mock_session.post.return_value = mock_response

        result = send_backchannel_logout_request(
            self.provider.pk, "http://testserver", sub="test-user-uid"
        )

        self.assertTrue(result)
        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args
        self.assertIn("logout_token", call_args[1]["data"])
        self.assertEqual(
            call_args[1]["headers"]["Content-Type"], "application/x-www-form-urlencoded"
        )

        # Scenario 2: Failed request (400 response)
        mock_session.post.reset_mock()
        mock_response.status_code = 400
        result = send_backchannel_logout_request(
            self.provider.pk, "http://testserver", sub="test-user-uid"
        )
        self.assertFalse(result)

        # Scenario 3: No URI configured
        mock_session.post.reset_mock()
        self.provider.backchannel_logout_uris = []
        self.provider.save()
        result = send_backchannel_logout_request(
            self.provider.pk, "http://testserver", sub="test-user-uid"
        )
        self.assertFalse(result)
        mock_session.post.assert_not_called()

        # Scenario 4: No subject provided
        result = send_backchannel_logout_request(self.provider.pk, "http://testserver")
        self.assertFalse(result)

        # Scenario 5: Non-existent provider
        result = send_backchannel_logout_request(
            99999, "http://testserver", sub="test-user-uid"
        )
        self.assertFalse(result)

        # Scenario 6: Request timeout
        from requests.exceptions import Timeout

        mock_session.post.side_effect = Timeout("Request timed out")
        self.provider.backchannel_logout_uris = [
            RedirectURI(RedirectURIMatchingMode.STRICT, "http://testserver/backchannel_logout")
        ]
        self.provider.save()
        result = send_backchannel_logout_request(
            self.provider.pk, "http://testserver", sub="test-user-uid"
        )
        self.assertFalse(result)

        # Scenario 7: Event creation
        mock_session.post.side_effect = None
        mock_session.post.reset_mock()
        mock_response.status_code = 200
        mock_session.post.return_value = mock_response

        initial_event_count = Event.objects.count()
        send_backchannel_logout_request(
            self.provider.pk, "http://testserver", sub="test-user-uid"
        )

        self.assertEqual(Event.objects.count(), initial_event_count + 1)
        event = Event.objects.latest("created")
        self.assertEqual(event.action, "custom_backchannel_logout")
        self.assertIn("Back-channel logout notification sent", event.context.get("message", ""))

    @patch("authentik.providers.oauth2.tasks.send_backchannel_logout_request.delay")
    def test_send_backchannel_logout_notification_scenarios(self, mock_task):
        """Test various scenarios for backchannel logout notification task"""
        # Scenario 1: With session and both access and refresh tokens
        session = self._create_session("test-session-123")

        # Create another OAuth2 provider to test multiple notifications
        provider2 = self._create_provider("provider2")

        # Create tokens for both providers
        self._create_token(self.provider, self.user, session, "access")
        self._create_token(provider2, self.user, session, "access")
        self._create_token(self.provider, self.user, session, "refresh")
        self._create_token(provider2, self.user, session, "refresh")

        send_backchannel_logout_notification(session=session)
        # Should call the task for each OAuth2 provider
        self.assertEqual(mock_task.call_count, 2)

        # Scenario 2: With access tokens only (no refresh tokens)
        mock_task.reset_mock()
        session2 = self._create_session("test-session-456")

        # Create ONLY access tokens
        self._create_token(self.provider, self.user, session2, "access")
        self._create_token(provider2, self.user, session2, "access")

        # Verify no refresh tokens exist
        self.assertEqual(RefreshToken.objects.filter(session=session2).count(), 0)

        send_backchannel_logout_notification(session=session2)
        # Should still call the task for each OAuth2 provider even without refresh tokens
        self.assertEqual(mock_task.call_count, 2)

        # Scenario 3: With user parameter
        # mock_task.reset_mock()
        # try:
        #     send_backchannel_logout_notification(user=self.user)
        # except Exception as e:
        #     self.fail(f"send_backchannel_logout_notification raised {e} unexpectedly")

        # Scenario 4: With no parameters
        mock_task.reset_mock()
        send_backchannel_logout_notification()
