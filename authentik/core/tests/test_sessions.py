"""Session browser grouping tests"""

from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils.crypto import get_random_string

from authentik.core.models import AuthenticatedSession
from authentik.core.sessions import (
    SessionStore,
    authenticated_session_from_request,
    bind_authenticated_session_to_browser,
)
from authentik.core.tests.utils import create_test_session, create_test_user
from authentik.root.middleware import (
    BROWSER_COOKIE_KEY_LENGTH,
    BROWSER_COOKIE_NAME,
    SessionMiddleware,
)


class TestSessionSuperseding(TestCase):
    """Test that logins a browser switched away from can't be replayed"""

    def setUp(self):
        self.user = create_test_user()

    def test_current_session_loads(self):
        """Test the current login of a browser keeps working"""
        target = create_test_session(
            self.user, browser_key=get_random_string(BROWSER_COOKIE_KEY_LENGTH)
        )
        self.client.cookies[settings.SESSION_COOKIE_NAME] = target.session.session_key

        response = self.client.get(reverse("authentik_api:user-me"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["username"], self.user.username)

    def test_existing_session_gets_browser_key(self):
        """Test an authenticated session without a browser key is bound on next request"""
        target = create_test_session(self.user)
        self.assertIsNone(target.browser_key)
        self.client.cookies[settings.SESSION_COOKIE_NAME] = target.session.session_key

        response = self.client.get(reverse("authentik_api:user-me"))

        self.assertEqual(response.status_code, 200)
        target.refresh_from_db()
        self.assertIsNotNone(target.browser_key)
        self.assertTrue(target.is_current)
        browser_cookie = response.cookies.get(BROWSER_COOKIE_NAME)
        self.assertIsNotNone(browser_cookie)
        self.assertEqual(
            SessionMiddleware.parse_browser_key(browser_cookie.value),
            target.browser_key,
        )

    def test_superseded_session_rejected(self):
        """Test a recorded session cookie can't be replayed after an account switch"""
        target = create_test_session(
            self.user, browser_key=get_random_string(BROWSER_COOKIE_KEY_LENGTH)
        )
        target.is_current = False
        target.save(update_fields=["is_current"])
        self.client.cookies[settings.SESSION_COOKIE_NAME] = target.session.session_key

        response = self.client.get(reverse("authentik_api:user-me"))

        self.assertEqual(response.status_code, 403)

    def test_login_supersedes_other_browser_sessions(self):
        """Test a new login marks the browser's previous logins as not current"""
        browser_key = get_random_string(BROWSER_COOKIE_KEY_LENGTH)
        previous = create_test_session(self.user, browser_key=browser_key)
        other_browser = create_test_session(
            self.user, browser_key=get_random_string(BROWSER_COOKIE_KEY_LENGTH)
        )
        target = create_test_session(self.user)
        original_save = AuthenticatedSession.save

        def fail_target_save(instance, *args, **kwargs):
            if instance.pk == target.pk:
                raise RuntimeError("activation failed")
            return original_save(instance, *args, **kwargs)

        request = RequestFactory().get("/")
        request.browser_key = browser_key
        with patch.object(
            AuthenticatedSession,
            "save",
            autospec=True,
            side_effect=fail_target_save,
        ):
            with self.assertRaises(RuntimeError):
                bind_authenticated_session_to_browser(request, target)
        previous.refresh_from_db()
        self.assertTrue(previous.is_current)

        request = RequestFactory().get("/")
        request.browser_key = browser_key
        request.session = SessionStore()
        request.session.create()
        new_session = authenticated_session_from_request(request, self.user)

        self.assertEqual(new_session.browser_key, browser_key)
        self.assertTrue(new_session.is_current)
        previous.refresh_from_db()
        self.assertFalse(previous.is_current)
        other_browser.refresh_from_db()
        self.assertTrue(other_browser.is_current)


class TestBrowserCookie(TestCase):
    """Test issuance and validation of the browser cookie"""

    def test_cookie_issued_alongside_session(self):
        """Test the browser cookie is set when a session with a browser key is saved"""

        def view(request):
            request.user = AnonymousUser()
            request.session["foo"] = "bar"
            SessionMiddleware.ensure_browser_key(request)
            return HttpResponse()

        response = SessionMiddleware(view)(RequestFactory().get("/"))

        cookie = response.cookies.get(BROWSER_COOKIE_NAME)
        self.assertIsNotNone(cookie)
        self.assertIsNotNone(SessionMiddleware.parse_browser_key(cookie.value))
        self.assertFalse(cookie["httponly"])

    def test_existing_cookie_reused(self):
        """Test an existing browser cookie is parsed onto the request"""
        browser_key = get_random_string(BROWSER_COOKIE_KEY_LENGTH)
        request = RequestFactory().get("/")
        request.COOKIES[BROWSER_COOKIE_NAME] = SessionMiddleware.encode_browser_key(browser_key)

        SessionMiddleware(lambda request: HttpResponse()).process_request(request)

        self.assertEqual(request.browser_key, browser_key)
        self.assertEqual(SessionMiddleware.ensure_browser_key(request), browser_key)

    def test_parse_browser_key(self):
        """Test browser cookie values are validated"""
        valid = get_random_string(BROWSER_COOKIE_KEY_LENGTH)
        token = SessionMiddleware.encode_browser_key(valid)
        self.assertEqual(SessionMiddleware.parse_browser_key(token), valid)
        self.assertIsNone(SessionMiddleware.parse_browser_key(valid))
        self.assertIsNone(SessionMiddleware.parse_browser_key(None))
        self.assertIsNone(SessionMiddleware.parse_browser_key(""))
        self.assertIsNone(SessionMiddleware.parse_browser_key("too-short"))
        self.assertIsNone(
            SessionMiddleware.parse_browser_key("x" * (BROWSER_COOKIE_KEY_LENGTH + 1))
        )
        self.assertIsNone(SessionMiddleware.parse_browser_key("!" * BROWSER_COOKIE_KEY_LENGTH))
