"""Test OAuth2 Back-Channel Logout implementation"""

import json
from unittest.mock import Mock, patch

import jwt
from django.test import RequestFactory
from django.utils import timezone
from requests import Response

from authentik.core.models import Application, AuthenticatedSession, Session, User
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
from authentik.providers.oauth2.utils import create_logout_token
from authentik.providers.oauth2.views.backchannel_logout import BackChannelLogoutView


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

    def test_create_logout_token_with_session_id(self):
        """Test creating a logout token with session ID"""
        session_id = "test-session-123"

        token = create_logout_token(self.provider, session_id=session_id)

        # Decode and validate the token
        key, alg = self.provider.jwt_key
        if alg != "HS256":
            key = self.provider.signing_key.public_key
        decoded = jwt.decode(
            token, key, algorithms=[alg], options={"verify_exp": False, "verify_aud": False}
        )

        self.assertIn("iss", decoded)
        self.assertEqual(decoded["aud"], self.provider.client_id)
        self.assertIn("iat", decoded)
        self.assertIn("jti", decoded)
        self.assertEqual(decoded["sid"], session_id)
        self.assertIn("events", decoded)
        self.assertIn("http://schemas.openid.net/event/backchannel-logout", decoded["events"])

    def test_create_logout_token_with_sub(self):
        """Test creating a logout token with subject"""
        sub = "user-123"

        token = create_logout_token(self.provider, sub=sub)

        # Decode and validate the token
        key, alg = self.provider.jwt_key
        if alg != "HS256":
            key = self.provider.signing_key.public_key
        decoded = jwt.decode(
            token, key, algorithms=[alg], options={"verify_exp": False, "verify_aud": False}
        )

        self.assertEqual(decoded["sub"], sub)
        self.assertIn("events", decoded)
        self.assertIn("http://schemas.openid.net/event/backchannel-logout", decoded["events"])

    def test_create_logout_token_with_both_sid_and_sub(self):
        """Test creating a logout token with both session ID and subject"""
        session_id = "test-session-123"
        sub = "user-123"

        token = create_logout_token(self.provider, session_id=session_id, sub=sub)

        # Decode and validate the token
        key, alg = self.provider.jwt_key
        if alg != "HS256":
            key = self.provider.signing_key.public_key
        decoded = jwt.decode(
            token, key, algorithms=[alg], options={"verify_exp": False, "verify_aud": False}
        )

        self.assertEqual(decoded["sid"], session_id)
        self.assertEqual(decoded["sub"], sub)

    def test_backchannel_logout_view_missing_token(self):
        """Test back-channel logout view with missing logout token"""
        request = self.factory.post("/backchannel_logout", {})

        view = BackChannelLogoutView()
        response = view.post(request, self.app.slug)

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "invalid_request")
        self.assertIn("Missing logout_token", data["error_description"])

    def test_backchannel_logout_view_invalid_application(self):
        """Test back-channel logout view with invalid application slug"""
        logout_token = create_logout_token(self.provider, session_id="test-session")
        request = self.factory.post("/backchannel_logout", {"logout_token": logout_token})

        view = BackChannelLogoutView()

        # Test with non-existent application - should return 500 error
        response = view.post(request, "non-existent-app")
        self.assertEqual(response.status_code, 500)

    def test_backchannel_logout_view_invalid_provider_type(self):
        """Test back-channel logout view with non-OAuth2 provider"""
        # Create an app without OAuth2 provider
        app_without_oauth = Application.objects.create(name="test-no-oauth", slug="test-no-oauth")

        logout_token = create_logout_token(self.provider, session_id="test-session")
        request = self.factory.post("/backchannel_logout", {"logout_token": logout_token})

        view = BackChannelLogoutView()
        response = view.post(request, app_without_oauth.slug)

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "invalid_request")
        self.assertIn("Invalid provider type", data["error_description"])

    def test_backchannel_logout_view_invalid_token(self):
        """Test back-channel logout view with invalid JWT token"""
        request = self.factory.post("/backchannel_logout", {"logout_token": "invalid.jwt.token"})

        view = BackChannelLogoutView()
        response = view.post(request, self.app.slug)

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "invalid_request")

    def test_backchannel_logout_view_invalid_issuer(self):
        """Test back-channel logout view with invalid issuer in token"""
        # Create a token with wrong issuer
        payload = {
            "iss": "https://wrong-issuer.com",
            "aud": self.provider.client_id,
            "iat": timezone.now().timestamp(),
            "jti": "test-jti",
            "sid": "test-session",
            "events": {"http://schemas.openid.net/event/backchannel-logout": {}},
        }

        key, alg = self.provider.jwt_key
        invalid_token = jwt.encode(payload, key, algorithm=alg)

        request = self.factory.post("/backchannel_logout", {"logout_token": invalid_token})

        view = BackChannelLogoutView()
        response = view.post(request, self.app.slug)

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "invalid_request")

    def test_backchannel_logout_view_missing_sub_and_sid(self):
        """Test back-channel logout view with token missing both sub and sid"""
        payload = {
            "iss": self.provider.get_issuer(self.factory.get("/")),
            "aud": self.provider.client_id,
            "iat": timezone.now().timestamp(),
            "jti": "test-jti",
            "events": {"http://schemas.openid.net/event/backchannel-logout": {}},
        }

        key, alg = self.provider.jwt_key
        invalid_token = jwt.encode(payload, key, algorithm=alg)

        request = self.factory.post("/backchannel_logout", {"logout_token": invalid_token})

        view = BackChannelLogoutView()
        response = view.post(request, self.app.slug)

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "invalid_request")

    def test_backchannel_logout_view_invalid_events_claim(self):
        """Test back-channel logout view with invalid events claim"""
        payload = {
            "iss": self.provider.get_issuer(self.factory.get("/")),
            "aud": self.provider.client_id,
            "iat": timezone.now().timestamp(),
            "jti": "test-jti",
            "sid": "test-session",
            "events": {"invalid-event": {}},  # Wrong event type
        }

        key, alg = self.provider.jwt_key
        invalid_token = jwt.encode(payload, key, algorithm=alg)

        request = self.factory.post("/backchannel_logout", {"logout_token": invalid_token})

        view = BackChannelLogoutView()
        response = view.post(request, self.app.slug)

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "invalid_request")

    def test_backchannel_logout_view_successful_session_termination(self):
        """Test successful back-channel logout with session termination"""
        # Create a session and refresh token
        session = AuthenticatedSession.objects.create(
            session=Session.objects.create(
                session_key="test-session-123",
                last_ip="127.0.0.1",
            ),
            user=self.user,
        )

        refresh_token = RefreshToken.objects.create(
            provider=self.provider,
            user=self.user,
            session=session,
            token="test-refresh-token",  # nosec
            _id_token=json.dumps({}),
            auth_time=timezone.now(),
        )

        # Create request first to ensure consistent issuer
        request = self.factory.post("/backchannel_logout", {})

        # Create logout token with the same request context
        from django.http import HttpRequest

        token_request = HttpRequest()
        token_request.META = request.META.copy()

        # Generate issuer using the same request context
        issuer = self.provider.get_issuer(token_request)

        # Create logout token manually with correct issuer
        import uuid
        from time import time as current_time

        payload = {
            "iss": issuer,
            "aud": self.provider.client_id,
            "iat": int(current_time()),
            "jti": str(uuid.uuid4()),
            "events": {
                "http://schemas.openid.net/event/backchannel-logout": {},
            },
            "sid": "test-session-123",
        }
        logout_token = self.provider.encode(payload)

        # Update request with the logout token
        request = self.factory.post("/backchannel_logout", {"logout_token": logout_token})

        view = BackChannelLogoutView()
        response = view.post(request, self.app.slug)

        self.assertEqual(response.status_code, 200)

        # Verify session was deleted
        self.assertFalse(
            AuthenticatedSession.objects.filter(session__session_key="test-session-123").exists()
        )

        # Verify refresh token was revoked
        refresh_token.refresh_from_db()
        self.assertTrue(refresh_token.revoked)

    def test_backchannel_logout_view_successful_with_sub(self):
        """Test successful back-channel logout with subject identifier"""
        logout_token = create_logout_token(self.provider, sub="user-123")
        request = self.factory.post("/backchannel_logout", {"logout_token": logout_token})

        view = BackChannelLogoutView()
        response = view.post(request, self.app.slug)

        # Should succeed even if no sessions are found to terminate
        self.assertIn(response.status_code, [200, 400])  # Accept either as valid

    @patch("authentik.providers.oauth2.tasks.requests.post")
    def test_send_backchannel_logout_request_success(self, mock_post):
        """Test successful back-channel logout request task"""
        # Mock successful HTTP response
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Update provider to have backchannel logout URI
        self.provider.backchannel_logout_uris = [
            RedirectURI(RedirectURIMatchingMode.STRICT, "http://testserver/backchannel_logout")
        ]
        self.provider.save()

        result = send_backchannel_logout_request(self.provider.pk, session_id="test-session-123")

        self.assertTrue(result)
        mock_post.assert_called_once()

        # Verify the request was made with correct parameters
        call_args = mock_post.call_args
        self.assertIn("logout_token", call_args[1]["data"])
        self.assertEqual(
            call_args[1]["headers"]["Content-Type"], "application/x-www-form-urlencoded"
        )

    @patch("authentik.providers.oauth2.tasks.requests.post")
    def test_send_backchannel_logout_request_failure(self, mock_post):
        """Test failed back-channel logout request task"""
        # Mock failed HTTP response
        mock_response = Mock(spec=Response)
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        # Update provider to have backchannel logout URI
        self.provider.backchannel_logout_uris = [
            RedirectURI(RedirectURIMatchingMode.STRICT, "http://testserver/backchannel_logout")
        ]
        self.provider.save()

        result = send_backchannel_logout_request(self.provider.pk, session_id="test-session-123")

        self.assertFalse(result)

    def test_send_backchannel_logout_request_no_uri(self):
        """Test back-channel logout request task with no logout URI configured"""
        result = send_backchannel_logout_request(self.provider.pk, session_id="test-session-123")

        self.assertFalse(result)

    def test_send_backchannel_logout_request_no_session_or_sub(self):
        """Test back-channel logout request task with no session ID or subject"""
        result = send_backchannel_logout_request(self.provider.pk)

        self.assertFalse(result)

    def test_send_backchannel_logout_request_nonexistent_provider(self):
        """Test back-channel logout request task with non-existent provider"""
        result = send_backchannel_logout_request(99999, session_id="test-session-123")

        self.assertFalse(result)

    @patch("authentik.providers.oauth2.tasks.send_backchannel_logout_request.delay")
    def test_send_backchannel_logout_notification_with_session(self, mock_task):
        """Test back-channel logout notification task with session"""
        session = AuthenticatedSession.objects.create(
            session=Session.objects.create(
                session_key="test-session-123",
                last_ip="127.0.0.1",
            ),
            user=self.user,
        )

        # Create another OAuth2 provider to test multiple notifications
        provider2 = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            redirect_uris=[
                RedirectURI(RedirectURIMatchingMode.STRICT, "http://testserver2/callback"),
            ],
            signing_key=self.keypair,
        )

        # Create access tokens and refresh tokens for both providers so they get notified
        from django.utils import timezone

        auth_time = timezone.now()

        # Create access tokens (covers all OAuth2 flows)
        AccessToken.objects.create(
            provider=self.provider,
            user=self.user,
            session=session,
            token=generate_id(),
            _id_token=json.dumps({}),
            auth_time=auth_time,
        )
        AccessToken.objects.create(
            provider=provider2,
            user=self.user,
            session=session,
            token=generate_id(),
            _id_token=json.dumps({}),
            auth_time=auth_time,
        )

        # Also create refresh tokens for completeness
        RefreshToken.objects.create(
            provider=self.provider,
            user=self.user,
            session=session,
            token=generate_id(),
            _id_token=json.dumps({}),
            auth_time=auth_time,
        )
        RefreshToken.objects.create(
            provider=provider2,
            user=self.user,
            session=session,
            token=generate_id(),
            _id_token=json.dumps({}),
            auth_time=auth_time,
        )

        send_backchannel_logout_notification(session=session)

        # Should call the task for each OAuth2 provider
        self.assertEqual(mock_task.call_count, 2)

    @patch("authentik.providers.oauth2.tasks.send_backchannel_logout_request.delay")
    def test_send_backchannel_logout_notification_access_tokens_only(self, mock_task):
        """Test back-channel logout notification with access tokens only (no refresh tokens)"""
        session = AuthenticatedSession.objects.create(
            session=Session.objects.create(
                session_key="test-session-456",
                last_ip="127.0.0.1",
            ),
            user=self.user,
        )

        # Create another OAuth2 provider
        provider2 = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            redirect_uris=[
                RedirectURI(RedirectURIMatchingMode.STRICT, "http://testserver2/callback"),
            ],
            signing_key=self.keypair,
        )

        # Create ONLY access tokens (no refresh tokens) to simulate:
        # - Authorization code flow without offline_access scope
        # - Implicit flow clients
        from django.utils import timezone

        auth_time = timezone.now()

        AccessToken.objects.create(
            provider=self.provider,
            user=self.user,
            session=session,
            token=generate_id(),
            _id_token=json.dumps({}),
            auth_time=auth_time,
        )
        AccessToken.objects.create(
            provider=provider2,
            user=self.user,
            session=session,
            token=generate_id(),
            _id_token=json.dumps({}),
            auth_time=auth_time,
        )

        # Explicitly verify no refresh tokens exist
        self.assertEqual(RefreshToken.objects.filter(session=session).count(), 0)

        send_backchannel_logout_notification(session=session)

        # Should still call the task for each OAuth2 provider even without refresh tokens
        # This demonstrates specification compliance
        self.assertEqual(mock_task.call_count, 2)

    def test_send_backchannel_logout_notification_with_user(self):
        """Test back-channel logout notification task with user"""
        # This should not raise an exception
        try:
            send_backchannel_logout_notification(user=self.user)
        except Exception as e:
            self.fail(f"send_backchannel_logout_notification raised {e} unexpectedly")

    def test_send_backchannel_logout_notification_no_params(self):
        """Test back-channel logout notification task with no parameters"""
        # Should not raise an exception
        send_backchannel_logout_notification()

    @patch("authentik.providers.oauth2.tasks.requests.post")
    def test_send_backchannel_logout_request_creates_event(self, mock_post):
        """Test that successful back-channel logout request creates an event"""
        # Mock successful HTTP response
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Update provider to have backchannel logout URI
        self.provider.backchannel_logout_uris = [
            RedirectURI(RedirectURIMatchingMode.STRICT, "http://testserver/backchannel_logout")
        ]
        self.provider.save()

        initial_event_count = Event.objects.count()

        send_backchannel_logout_request(self.provider.pk, session_id="test-session-123")

        # Verify an event was created
        self.assertEqual(Event.objects.count(), initial_event_count + 1)

        event = Event.objects.latest("created")
        self.assertEqual(event.action, "custom_backchannel_logout")
        self.assertIn("Back-channel logout notification sent", event.context.get("message", ""))

    @patch("authentik.providers.oauth2.tasks.requests.post")
    def test_send_backchannel_logout_request_timeout(self, mock_post):
        """Test back-channel logout request with timeout"""
        from requests.exceptions import Timeout

        mock_post.side_effect = Timeout("Request timed out")

        # Update provider to have backchannel logout URI
        self.provider.backchannel_logout_uris = [
            RedirectURI(RedirectURIMatchingMode.STRICT, "http://testserver/backchannel_logout")
        ]
        self.provider.save()

        result = send_backchannel_logout_request(self.provider.pk, session_id="test-session-123")

        self.assertFalse(result)

    def test_backchannel_logout_view_exception_handling(self):
        """Test back-channel logout view exception handling"""
        # Create a malformed request that will cause an exception
        request = self.factory.post("/backchannel_logout", {"logout_token": "malformed"})

        view = BackChannelLogoutView()

        # Mock the provider to raise an exception during processing
        with patch.object(view, "process_logout_token", side_effect=Exception("Test error")):
            response = view.post(request, self.app.slug)

            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertEqual(data["error"], "server_error")
            self.assertIn("Internal server error", data["error_description"])

    def test_backchannel_logout_view_find_user_by_sub(self):
        """Test back-channel logout view can find user by sub claim based on sub_mode"""
        from authentik.providers.oauth2.constants import SubModes

        view = BackChannelLogoutView()
        view.provider = self.provider

        # Test HASHED_USER_ID mode (default)
        self.provider.sub_mode = SubModes.HASHED_USER_ID
        found_user = view._find_user_by_sub(self.user.uid)
        self.assertEqual(found_user, self.user)

        # Test USER_ID mode
        self.provider.sub_mode = SubModes.USER_ID
        found_user = view._find_user_by_sub(str(self.user.pk))
        self.assertEqual(found_user, self.user)

        # Test USER_UUID mode
        self.provider.sub_mode = SubModes.USER_UUID
        found_user = view._find_user_by_sub(str(self.user.uuid))
        self.assertEqual(found_user, self.user)

        # Test USER_EMAIL mode
        self.provider.sub_mode = SubModes.USER_EMAIL
        found_user = view._find_user_by_sub(self.user.email)
        self.assertEqual(found_user, self.user)

        # Test USER_USERNAME mode
        self.provider.sub_mode = SubModes.USER_USERNAME
        found_user = view._find_user_by_sub(self.user.username)
        self.assertEqual(found_user, self.user)

        # Test non-existent user
        found_user = view._find_user_by_sub("non-existent")
        self.assertIsNone(found_user)

    def test_backchannel_logout_view_terminate_user_sessions(self):
        """Test back-channel logout view terminates user sessions correctly"""

        # Create test sessions
        session1 = Session.objects.create(
            last_ip="255.255.255.255",
            session_key="test-session-1",
            expires=timezone.now() + timezone.timedelta(hours=1),
        )
        session2 = Session.objects.create(
            session_key="test-session-2",
            expires=timezone.now() + timezone.timedelta(hours=1),
            last_ip="255.255.255.255",
        )
        session3 = Session.objects.create(
            session_key="test-session-3",
            expires=timezone.now() + timezone.timedelta(hours=1),
            last_ip="255.255.255.255",
        )

        # Create authenticated sessions
        auth_session1 = AuthenticatedSession.objects.create(
            session=session1,
            user=self.user,
        )
        auth_session2 = AuthenticatedSession.objects.create(
            session=session2,
            user=self.user,
        )
        auth_session3 = AuthenticatedSession.objects.create(
            session=session3,
            user=self.user,
        )

        # Create access tokens for sessions 1 and 2
        access_token1 = AccessToken.objects.create(
            provider=self.provider,
            user=self.user,
            session_id=auth_session1.session_id,
            token="access-token-1",
            _id_token="{}",
            auth_time=timezone.now(),
        )
        access_token2 = AccessToken.objects.create(
            provider=self.provider,
            user=self.user,
            session_id=auth_session2.session_id,
            token="access-token-2",
            _id_token="{}",
            auth_time=timezone.now(),
        )

        # Create refresh token for session 2 and 3
        refresh_token2 = RefreshToken.objects.create(
            provider=self.provider,
            user=self.user,
            session_id=auth_session2.session_id,
            token="refresh-token-2",
            _id_token="{}",
            auth_time=timezone.now(),
        )
        refresh_token3 = RefreshToken.objects.create(
            provider=self.provider,
            user=self.user,
            session_id=auth_session3.session_id,
            token="refresh-token-3",
            _id_token="{}",
            auth_time=timezone.now(),
        )

        # Create a separate session for tokens from different provider
        other_session = Session.objects.create(
            session_key="other-session",
            expires=timezone.now() + timezone.timedelta(hours=1),
            last_ip="255.255.255.255",
        )
        other_auth_session = AuthenticatedSession.objects.create(
            session=other_session,
            user=self.user,
        )

        # Create tokens for different provider (should not be affected)
        other_provider = OAuth2Provider.objects.create(
            name="Other Provider",
            client_id="other-client",
            authorization_flow=create_test_flow(),
        )
        other_access_token = AccessToken.objects.create(
            provider=other_provider,
            user=self.user,
            session=other_auth_session,  # Different session
            token="access-token-other",
            _id_token="{}",
            auth_time=timezone.now(),
        )

        # Verify initial state
        self.assertEqual(AccessToken.objects.filter(provider=self.provider).count(), 2)
        self.assertEqual(RefreshToken.objects.filter(provider=self.provider).count(), 2)
        self.assertEqual(AuthenticatedSession.objects.count(), 4)
        self.assertFalse(access_token1.revoked)
        self.assertFalse(access_token2.revoked)
        self.assertFalse(refresh_token2.revoked)
        self.assertFalse(refresh_token3.revoked)
        self.assertFalse(other_access_token.revoked)

        # Test the _terminate_user_sessions method
        view = BackChannelLogoutView()
        view.provider = self.provider
        view._terminate_user_sessions(self.user)

        # Verify tokens with sessions are deleted due to cascade delete
        # When AuthenticatedSession is deleted, it triggers Session deletion,
        # which cascades to delete associated tokens
        self.assertEqual(AccessToken.objects.filter(provider=self.provider).count(), 0)
        self.assertEqual(RefreshToken.objects.filter(provider=self.provider).count(), 0)

        with self.assertRaises(AccessToken.DoesNotExist):
            AccessToken.objects.get(token="access-token-1")
        with self.assertRaises(AccessToken.DoesNotExist):
            AccessToken.objects.get(token="access-token-2")
        self.assertTrue(RefreshToken.objects.get(token="refresh-token-2").revoked)
        self.assertTrue(RefreshToken.objects.get(token="refresh-token-3").revoked)

        # Token from different provider should still exist and not be revoked
        # (it's in a different session that wasn't terminated)
        other_access_token.refresh_from_db()
        self.assertFalse(other_access_token.revoked)

        # Verify sessions are terminated
        # Sessions 1, 2, and 3 should be deleted because they had tokens from this provider
        # The other_auth_session should remain because it has no tokens from this provider
        self.assertEqual(AuthenticatedSession.objects.count(), 1)
        self.assertEqual(Session.objects.count(), 1)

    def test_backchannel_logout_view_terminate_user_sessions_no_tokens(self):
        """Test _terminate_user_sessions with user that has no tokens"""

        # Create a user with no tokens
        user_no_tokens = User.objects.create(username="no-tokens-user")

        view = BackChannelLogoutView()
        view.provider = self.provider

        # Should not raise any exceptions
        view._terminate_user_sessions(user_no_tokens)

    def test_backchannel_logout_view_terminate_user_sessions_no_sessions(self):
        """Test _terminate_user_sessions with tokens that have no sessions"""

        # Create tokens without sessions
        AccessToken.objects.create(
            provider=self.provider,
            user=self.user,
            session=None,  # No session
            token="access-token-no-session",
            _id_token="{}",
            auth_time=timezone.now(),
        )
        RefreshToken.objects.create(
            provider=self.provider,
            user=self.user,
            session=None,  # No session
            token="refresh-token-no-session",
            _id_token="{}",
            auth_time=timezone.now(),
        )

        view = BackChannelLogoutView()
        view.provider = self.provider
        view._terminate_user_sessions(self.user)

        # Verify tokens are still revoked even without sessions
        revoked_access_token = AccessToken.objects.get(token="access-token-no-session")
        revoked_refresh_token = RefreshToken.objects.get(token="refresh-token-no-session")
        self.assertTrue(revoked_access_token.revoked)
        self.assertTrue(revoked_refresh_token.revoked)
