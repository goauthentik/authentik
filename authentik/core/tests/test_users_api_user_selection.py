"""Test user selection behavior."""

from urllib.parse import urlparse

from rest_framework.test import APITestCase

from authentik.common.oauth.constants import QS_LOGIN_HINT
from authentik.core.user_selection import PLAN_CONTEXT_ACCOUNT_SWITCH
from authentik.core.tests.user_selection import (
    create_browser_session,
    create_test_user_selection_flow,
    flow_executor_url,
    select_user_response,
)
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, PLAN_CONTEXT_REDIRECT
from authentik.flows.stage import PLAN_CONTEXT_PENDING_USER_IDENTIFIER
from authentik.flows.views.executor import SESSION_KEY_PLAN


class TestUsersAPIUserSelection(APITestCase):
    """Test user API user selection behavior."""

    def setUp(self) -> None:
        self.admin = create_test_admin_user()
        self.user = create_test_user()

    def test_user_selection_other_user_starts_authentication(self):
        """Test selecting another browser-local login starts account-switch authentication."""
        flow, _ = create_test_user_selection_flow()
        self.client.force_login(self.admin)
        create_browser_session(self, self.user)

        self.client.get(flow_executor_url(flow))
        response = self.client.post(
            flow_executor_url(flow),
            data=select_user_response(self.user),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/api/v3/flows/executor/", urlparse(response.url).path)
        plan = self.client.session[SESSION_KEY_PLAN]
        self.assertTrue(plan.context[PLAN_CONTEXT_ACCOUNT_SWITCH])
        self.assertEqual(plan.context[PLAN_CONTEXT_PENDING_USER].pk, self.user.pk)
        self.assertEqual(plan.context[PLAN_CONTEXT_PENDING_USER_IDENTIFIER], self.user.email)
        self.assertEqual(plan.context[PLAN_CONTEXT_REDIRECT], "/")

    def test_user_selection_signed_out_requires_login(self):
        """Test a signed-out browser has to authenticate to use one of its logins."""
        flow, _ = create_test_user_selection_flow()
        create_browser_session(self, self.user)

        challenge = self.client.get(flow_executor_url(flow))
        self.assertNotIn("authentication", challenge.json()["accounts"][0])
        response = self.client.post(
            flow_executor_url(flow),
            data=select_user_response(self.user),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/api/v3/flows/executor/", urlparse(response.url).path)
        plan = self.client.session[SESSION_KEY_PLAN]
        self.assertTrue(plan.context[PLAN_CONTEXT_ACCOUNT_SWITCH])
        self.assertEqual(plan.context[PLAN_CONTEXT_PENDING_USER].pk, self.user.pk)
        self.assertEqual(plan.context[PLAN_CONTEXT_PENDING_USER_IDENTIFIER], self.user.email)
        self.assertEqual(plan.context[PLAN_CONTEXT_REDIRECT], "/")

    def test_user_selection_current_user_continues(self):
        """Test selecting the current user continues the user-selection flow."""
        flow, _ = create_test_user_selection_flow()
        self.client.force_login(self.admin)
        create_browser_session(self, self.user)

        self.client.get(flow_executor_url(flow))
        response = self.client.post(
            flow_executor_url(flow),
            data=select_user_response(self.admin),
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
