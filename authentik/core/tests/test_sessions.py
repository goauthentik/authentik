"""Session browser binding tests"""

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils.crypto import get_random_string

from authentik.core.tests.user_selection import create_browser_session
from authentik.core.tests.utils import create_test_user
from authentik.root.middleware import BROWSER_KEY_LENGTH, COOKIE_NAME_BROWSER, SessionMiddleware


class TestSessionBrowserBinding(TestCase):
    """Test that browser-bound sessions can only be used with their browser cookie"""

    def setUp(self):
        self.user = create_test_user()

    def test_bound_session_requires_browser_cookie(self):
        """Test a browser-bound session only loads with the matching browser cookie"""
        target = create_browser_session(self, self.user)
        self.client.cookies[settings.SESSION_COOKIE_NAME] = target.session.session_key

        response = self.client.get(reverse("authentik_api:user-me"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["username"], self.user.username)

        self.client.cookies[settings.SESSION_COOKIE_NAME] = target.session.session_key
        self.client.cookies.pop(COOKIE_NAME_BROWSER)
        response = self.client.get(reverse("authentik_api:user-me"))
        self.assertEqual(response.status_code, 403)

    def test_bound_session_rejects_other_browser_cookie(self):
        """Test a browser-bound session doesn't load with a different browser cookie"""
        target = create_browser_session(self, self.user)
        self.client.cookies[settings.SESSION_COOKIE_NAME] = target.session.session_key
        self.client.cookies[COOKIE_NAME_BROWSER] = get_random_string(BROWSER_KEY_LENGTH)

        response = self.client.get(reverse("authentik_api:user-me"))

        self.assertEqual(response.status_code, 403)

    def test_unbound_session_loads_without_browser_cookie(self):
        """Test sessions without a browser binding (e.g. pre-existing ones) keep working"""
        self.client.force_login(self.user)

        response = self.client.get(reverse("authentik_api:user-me"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["username"], self.user.username)

    def test_parse_browser_key(self):
        """Test browser cookie values are validated"""
        valid = get_random_string(BROWSER_KEY_LENGTH)
        self.assertEqual(SessionMiddleware.parse_browser_key(valid), valid)
        self.assertIsNone(SessionMiddleware.parse_browser_key(None))
        self.assertIsNone(SessionMiddleware.parse_browser_key(""))
        self.assertIsNone(SessionMiddleware.parse_browser_key("too-short"))
        self.assertIsNone(SessionMiddleware.parse_browser_key("x" * (BROWSER_KEY_LENGTH + 1)))
        self.assertIsNone(SessionMiddleware.parse_browser_key("!" * BROWSER_KEY_LENGTH))
