"""Test user API user selection behavior."""

from json import dumps as json_dumps
from urllib.parse import parse_qs, urlparse

from django.conf import settings
from django.urls.base import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from authentik.common.oauth.constants import QS_LOGIN_HINT
from authentik.core.tests.user_selection import (
    create_browser_session,
    create_test_user_selection_flow,
    flow_executor_url,
)
from authentik.core.tests.utils import create_test_admin_user, create_test_user


class TestUsersAPIUserSelection(APITestCase):
    """Test user API user selection behavior."""

    def setUp(self) -> None:
        self.admin = create_test_admin_user()
        self.user = create_test_user()

    def test_user_me_lists_browser_sessions(self):
        """Test user/me lists the live logins of this browser."""
        self.client.force_login(self.admin)
        create_browser_session(self, self.user)

        response = self.client.get(reverse("authentik_api:user-me"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [account["username"] for account in response.json()["accounts"]],
            [self.admin.username, self.user.username],
        )
        self.assertTrue(response.json()["accounts"][0]["is_current"])
        self.assertEqual(response.json()["accounts"][0]["authentication"], "authenticated")
        self.assertFalse(response.json()["accounts"][1]["is_current"])
        self.assertEqual(response.json()["accounts"][1]["authentication"], "authenticated")

    def test_user_me_excludes_expired_sessions(self):
        """Test user/me doesn't list logins whose session has expired."""
        self.client.force_login(self.admin)
        expired = create_browser_session(self, self.user)
        expired.session.expires = timezone.now()
        expired.session.save()

        response = self.client.get(reverse("authentik_api:user-me"))

        self.assertEqual(
            [account["username"] for account in response.json()["accounts"]],
            [self.admin.username],
        )

    def test_user_me_excludes_other_browsers(self):
        """Test user/me doesn't list logins bound to a different browser."""
        self.client.force_login(self.admin)
        other_browser = create_browser_session(self, self.user)
        other_browser.browser_key = "x" * 32
        other_browser.save()

        response = self.client.get(reverse("authentik_api:user-me"))

        self.assertEqual(
            [account["username"] for account in response.json()["accounts"]],
            [self.admin.username],
        )

    def test_user_selection_other_user_switches_session(self):
        """Test selecting another live login switches to its session without authentication."""
        flow, _ = create_test_user_selection_flow()
        self.client.force_login(self.admin)
        target = create_browser_session(self, self.user)
        current_session_cookie = self.client.cookies[settings.SESSION_COOKIE_NAME].value

        self.client.get(flow_executor_url(flow))
        response = self.client.post(
            flow_executor_url(flow),
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
        self.assertNotEqual(
            self.client.cookies[settings.SESSION_COOKIE_NAME].value,
            current_session_cookie,
        )
        self.assertEqual(
            self.client.cookies[settings.SESSION_COOKIE_NAME].value,
            target.session.session_key,
        )
        response = self.client.get(reverse("authentik_api:user-me"))
        self.assertEqual(response.json()["user"]["username"], self.user.username)

    def test_user_selection_signed_out_requires_login(self):
        """Test a signed-out browser has to authenticate to use one of its logins."""
        flow, _ = create_test_user_selection_flow()
        create_browser_session(self, self.user)

        challenge = self.client.get(flow_executor_url(flow))
        self.assertEqual(
            [account["authentication"] for account in challenge.json()["accounts"]],
            ["remembered"],
        )
        response = self.client.post(
            flow_executor_url(flow),
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

    def test_user_selection_current_user_continues(self):
        """Test selecting the current user continues the user-selection flow."""
        flow, _ = create_test_user_selection_flow()
        self.client.force_login(self.admin)
        create_browser_session(self, self.user)

        self.client.get(flow_executor_url(flow))
        response = self.client.post(
            flow_executor_url(flow),
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
        """Test user selection hints matching browser logins."""
        flow, _ = create_test_user_selection_flow()
        self.client.force_login(self.admin)
        create_browser_session(self, self.user)

        response = self.client.get(
            flow_executor_url(flow),
            data={QS_LOGIN_HINT: self.user.email},
        )

        self.assertEqual(response.status_code, 200)
        accounts = response.json()["accounts"]
        self.assertEqual(accounts[0]["username"], self.user.username)
        self.assertTrue(accounts[0]["is_hint"])
