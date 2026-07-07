"""Session user switching tests"""

from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.db import IntegrityError
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils.crypto import get_random_string

from authentik.core import user_switching
from authentik.core.models import AuthenticatedSession
from authentik.core.sessions import SessionStore
from authentik.core.tests.utils import create_test_session, create_test_user
from authentik.root.middleware import SessionMiddleware


class TestSessionSuperseding(TestCase):
    """Test that logins a browser switched away from can't be replayed"""

    def setUp(self):
        self.user = create_test_user()

    def test_current_session_loads(self):
        """Test the current login of a browser keeps working"""
        target = create_test_session(
            self.user, user_switching_token=get_random_string(user_switching.TOKEN_LENGTH)
        )
        self.client.cookies[settings.SESSION_COOKIE_NAME] = target.session.session_key

        response = self.client.get(reverse("authentik_api:user-me"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["username"], self.user.username)

    def test_existing_session_gets_user_switching_token(self):
        """Test an authenticated session without a user switching token is
        bound on next request"""
        target = create_test_session(self.user)
        self.assertIsNone(target.user_switching_token)
        self.client.cookies[settings.SESSION_COOKIE_NAME] = target.session.session_key

        response = self.client.get(reverse("authentik_api:user-me"))

        self.assertEqual(response.status_code, 200)
        target.refresh_from_db()
        self.assertIsNotNone(target.user_switching_token)
        self.assertTrue(target.is_current)
        user_switching_cookie = response.cookies.get(user_switching.COOKIE_NAME)
        self.assertIsNotNone(user_switching_cookie)
        self.assertEqual(
            user_switching.decode_cookie(user_switching_cookie.value),
            target.user_switching_token,
        )

    def test_superseded_session_rejected(self):
        """Test a recorded session cookie can't be replayed after a user switch"""
        target = create_test_session(
            self.user, user_switching_token=get_random_string(user_switching.TOKEN_LENGTH)
        )
        target.is_current = False
        target.save(update_fields=["is_current"])
        self.client.cookies[settings.SESSION_COOKIE_NAME] = target.session.session_key

        response = self.client.get(reverse("authentik_api:user-me"))

        self.assertEqual(response.status_code, 403)

    def test_login_supersedes_other_browser_sessions(self):
        """Test a new login marks the browser's previous logins as not current"""
        user_switching_token = get_random_string(user_switching.TOKEN_LENGTH)
        previous = create_test_session(self.user, user_switching_token=user_switching_token)
        other_browser = create_test_session(
            self.user, user_switching_token=get_random_string(user_switching.TOKEN_LENGTH)
        )
        target = create_test_session(self.user)
        original_save = AuthenticatedSession.save

        def fail_target_save(instance, *args, **kwargs):
            if instance.pk == target.pk:
                raise RuntimeError("activation failed")
            return original_save(instance, *args, **kwargs)

        request = RequestFactory().get("/")
        request.user_switching_token = user_switching_token
        with patch.object(
            AuthenticatedSession,
            "save",
            autospec=True,
            side_effect=fail_target_save,
        ):
            with self.assertRaises(RuntimeError):
                target.bind_to_user_switching_token(user_switching_token)
        previous.refresh_from_db()
        self.assertTrue(previous.is_current)

        request = RequestFactory().get("/")
        request.user_switching_token = user_switching_token
        request.session = SessionStore()
        request.session.create()
        new_session = AuthenticatedSession.create_from_request(request, self.user)

        self.assertEqual(new_session.user_switching_token, user_switching_token)
        self.assertTrue(new_session.is_current)
        previous.refresh_from_db()
        self.assertFalse(previous.is_current)
        other_browser.refresh_from_db()
        self.assertTrue(other_browser.is_current)

    def test_bind_conflict_is_raised(self):
        """Test a lost race on the current-session constraint is surfaced."""
        token = get_random_string(user_switching.TOKEN_LENGTH)
        target = create_test_session(self.user, is_current=False)
        calls = []

        def failing_save(instance, *args, **kwargs):
            calls.append(instance.pk)
            raise IntegrityError("duplicate current session")

        with patch.object(
            AuthenticatedSession,
            "save",
            autospec=True,
            side_effect=failing_save,
        ):
            with self.assertRaises(IntegrityError):
                target.bind_to_user_switching_token(token)

        self.assertEqual(len(calls), 1)
        target.refresh_from_db()
        self.assertIsNone(target.user_switching_token)
        self.assertFalse(target.is_current)


class TestUserSwitchingCookie(TestCase):
    """Test issuance and validation of the user-switching cookie"""

    def test_cookie_issued_alongside_session(self):
        """Test the user-switching cookie is set when a session with an
        user switching token is saved"""

        def view(request):
            request.user = AnonymousUser()
            request.session["foo"] = "bar"
            user_switching.ensure_request_token(request)
            return HttpResponse()

        response = SessionMiddleware(view)(RequestFactory().get("/"))

        cookie = response.cookies.get(user_switching.COOKIE_NAME)
        self.assertIsNotNone(cookie)
        self.assertIsNotNone(user_switching.decode_cookie(cookie.value))
        self.assertFalse(cookie["httponly"])

    def test_existing_cookie_reused(self):
        """Test an existing user-switching cookie is parsed onto the request"""
        user_switching_token = get_random_string(user_switching.TOKEN_LENGTH)
        request = RequestFactory().get("/")
        request.COOKIES[user_switching.COOKIE_NAME] = user_switching.encode_cookie(
            user_switching_token
        )

        SessionMiddleware(lambda request: HttpResponse()).process_request(request)

        self.assertEqual(request.user_switching_token, user_switching_token)
        self.assertEqual(user_switching.ensure_request_token(request), user_switching_token)

    def test_existing_cookie_skips_authenticated_session_reconcile(self):
        """Test an existing switch token avoids per-response session lookups."""
        request = RequestFactory().get("/")
        request.session = SessionStore()
        request.session.create()
        request.user_switching_token = get_random_string(user_switching.TOKEN_LENGTH)
        request.user_switching_token_needs_update = False

        with patch("authentik.core.models.AuthenticatedSession.objects.filter") as filter_mock:
            SessionMiddleware.ensure_authenticated_session_user_switching_token(request)

        filter_mock.assert_not_called()

    def test_decode_cookie(self):
        """Test user-switching cookie values are validated"""
        valid = get_random_string(user_switching.TOKEN_LENGTH)
        token = user_switching.encode_cookie(valid)
        self.assertEqual(user_switching.decode_cookie(token), valid)
        self.assertIsNone(user_switching.decode_cookie(valid))
        self.assertIsNone(user_switching.decode_cookie(None))
        self.assertIsNone(user_switching.decode_cookie(""))
        self.assertIsNone(user_switching.decode_cookie("too-short"))
        self.assertIsNone(user_switching.decode_cookie("x" * (user_switching.TOKEN_LENGTH + 1)))
        self.assertIsNone(user_switching.decode_cookie("!" * user_switching.TOKEN_LENGTH))
