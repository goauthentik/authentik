"""Test user API user selection behavior."""

from json import dumps as json_dumps
from urllib.parse import parse_qs, urlparse

from django.conf import settings
from django.urls.base import reverse
from rest_framework.test import APITestCase

from authentik.common.oauth.constants import QS_LOGIN_HINT
from authentik.core.tests.user_selection import (
    create_test_user_selection_flow,
    remember_known_users,
)
from authentik.core.tests.utils import create_test_admin_user, create_test_user


class TestUsersAPIUserSelection(APITestCase):
    """Test user API user selection behavior."""

    def setUp(self) -> None:
        self.admin = create_test_admin_user()
        self.user = create_test_user()

    def test_user_me_user_selection(self):
        """Test user/me includes the browser-local user selection list."""
        self.client.force_login(self.admin)
        remember_known_users(self, self.admin, self.user)

        response = self.client.get(reverse("authentik_api:user-me"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [account["username"] for account in response.json()["accounts"]],
            [self.admin.username, self.user.username],
        )
        self.assertTrue(response.json()["accounts"][0]["is_current"])
        self.assertEqual(response.json()["accounts"][0]["authentication"], "authenticated")
        self.assertFalse(response.json()["accounts"][1]["is_current"])
        self.assertEqual(response.json()["accounts"][1]["authentication"], "remembered")

    def test_user_selection_other_user_requires_login(self):
        """Test selecting another remembered user starts authentication without switching."""
        flow, _ = create_test_user_selection_flow()
        self.client.force_login(self.admin)
        remember_known_users(self, self.admin, self.user)
        current_session_cookie = self.client.cookies[settings.SESSION_COOKIE_NAME].value

        self.client.get(reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}))
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            data=json_dumps(
                {
                    "component": "ak-stage-user-selection",
                    "action": "continue",
                    "selected_user": self.user.uuid.hex,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["component"], "xak-flow-redirect")
        self.assertEqual(
            urlparse(response.json()["to"]).path,
            reverse("authentik_flows:default-authentication"),
        )
        parsed = parse_qs(urlparse(response.json()["to"]).query)
        self.assertEqual(parsed[QS_LOGIN_HINT], [self.user.email])
        self.assertEqual(
            self.client.cookies[settings.SESSION_COOKIE_NAME].value,
            current_session_cookie,
        )
        response = self.client.get(reverse("authentik_api:user-me"))
        self.assertEqual(response.json()["user"]["username"], self.admin.username)

    def test_user_selection_current_user_continues(self):
        """Test selecting the current user continues the user-selection flow."""
        flow, _ = create_test_user_selection_flow()
        self.client.force_login(self.admin)
        remember_known_users(self, self.admin, self.user)

        self.client.get(reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}))
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            data=json_dumps(
                {
                    "component": "ak-stage-user-selection",
                    "action": "continue",
                    "selected_user": self.admin.uuid.hex,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["component"], "xak-flow-redirect")

    def test_user_selection_marks_login_hint_user(self):
        """Test user selection hints matching remembered users."""
        flow, _ = create_test_user_selection_flow()
        self.client.force_login(self.admin)
        remember_known_users(self, self.admin, self.user)

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            data={QS_LOGIN_HINT: self.user.email},
        )

        self.assertEqual(response.status_code, 200)
        accounts = response.json()["accounts"]
        self.assertEqual(accounts[0]["username"], self.user.username)
        self.assertTrue(accounts[0]["is_hint"])
