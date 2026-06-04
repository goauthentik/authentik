"""Test user API account selection behavior."""

from django.conf import settings
from django.urls.base import reverse
from rest_framework.test import APITestCase

from authentik.common.oauth.constants import QS_LOGIN_HINT
from authentik.core.account_selection import QS_ADD_ACCOUNT
from authentik.core.models import Session
from authentik.core.tests.account_selection import (
    create_test_account_selection_flow,
    remember_live_accounts,
)
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.flows.models import FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.generators import generate_id
from authentik.stages.authenticator_validate.models import AuthenticatorValidateStage


class TestUsersAPIAccountSelection(APITestCase):
    """Test user API account selection behavior."""

    def setUp(self) -> None:
        self.admin = create_test_admin_user()
        self.user = create_test_user()

    def test_user_me_account_selection(self):
        """Test user/me includes the browser-local account selection list."""
        remember_live_accounts(self, self.admin, self.user)
        response = self.client.get(reverse("authentik_api:user-me"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [account["username"] for account in response.json()["accounts"]],
            [self.admin.username, self.user.username],
        )
        self.assertTrue(response.json()["accounts"][0]["is_current"])
        self.assertFalse(response.json()["accounts"][1]["is_current"])

    def test_default_authentication_switches_live_account(self):
        """Test selecting a remembered account switches through the brand flow."""
        flow, selection_stage, switch_stage = create_test_account_selection_flow()
        accounts = remember_live_accounts(self, self.admin, self.user)
        response = self.client.get(
            reverse("authentik_flows:default-authentication"),
            data={"account_uid": self.user.uuid.hex, "next": "/"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(
            reverse("authentik_core:if-flow", kwargs={"flow_slug": flow.slug}),
            response.url,
        )
        plan = self.client.session[SESSION_KEY_PLAN]
        self.assertEqual(
            [binding.stage for binding in plan.bindings],
            [selection_stage, switch_stage],
        )

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug})
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            self.client.session[SESSION_KEY_PLAN].context[PLAN_CONTEXT_PENDING_USER],
            self.user,
        )
        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["component"], "xak-flow-redirect")
        self.assertEqual(response.json()["to"], "/")
        self.assertEqual(
            response.cookies[settings.SESSION_COOKIE_NAME].value,
            accounts[1]["session"],
        )
        response = self.client.get(reverse("authentik_api:user-me"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["username"], self.user.username)

    def test_default_authentication_switch_preserves_mfa_stage(self):
        """Test remembered account switches keep MFA stages before activating the session."""
        flow, selection_stage, switch_stage = create_test_account_selection_flow()
        mfa_stage = AuthenticatorValidateStage.objects.create(name=generate_id())
        FlowStageBinding.objects.create(target=flow, stage=mfa_stage, order=20)
        remember_live_accounts(self, self.admin, self.user)

        response = self.client.get(
            reverse("authentik_flows:default-authentication"),
            data={"account_uid": self.user.uuid.hex, "next": "/"},
        )

        self.assertEqual(response.status_code, 302)
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug})
        )
        self.assertEqual(response.status_code, 302)
        plan = self.client.session[SESSION_KEY_PLAN]
        self.assertEqual(plan.context[PLAN_CONTEXT_PENDING_USER], self.user)
        self.assertEqual([binding.stage for binding in plan.bindings], [mfa_stage, switch_stage])
        self.assertNotIn(selection_stage, [binding.stage for binding in plan.bindings])

    def test_default_authentication_marks_login_hint_account(self):
        """Test account selection hints matching remembered accounts."""
        flow, _, _ = create_test_account_selection_flow()
        remember_live_accounts(self, self.admin, self.user)

        response = self.client.get(
            reverse("authentik_flows:default-authentication"),
            data={QS_LOGIN_HINT: self.user.email, "next": "/"},
        )

        self.assertEqual(response.status_code, 302)
        challenge_response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug})
        )
        self.assertEqual(challenge_response.status_code, 200)
        accounts = challenge_response.json()["accounts"]
        self.assertEqual(accounts[0]["username"], self.user.username)
        self.assertTrue(accounts[0]["is_hint"])

    def test_default_authentication_add_account_uses_fresh_session(self):
        """Test adding another account doesn't destroy the current account session."""
        accounts = remember_live_accounts(self, self.admin)
        response = self.client.get(
            reverse("authentik_flows:default-authentication"),
            data={QS_ADD_ACCOUNT: "true", "next": "/"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Session.objects.filter(session_key=accounts[0]["session"]).exists())
        new_session_key = response.cookies[settings.SESSION_COOKIE_NAME].value
        self.assertNotEqual(new_session_key, accounts[0]["session"])
        self.assertTrue(Session.objects.filter(session_key=new_session_key).exists())
        self.assertNotIn(QS_ADD_ACCOUNT, response.url)
