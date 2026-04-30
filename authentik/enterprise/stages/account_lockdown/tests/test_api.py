"""Test Users Account Lockdown API"""

from json import loads
from unittest.mock import MagicMock, patch
from urllib.parse import urlparse

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import (
    create_test_brand,
    create_test_flow,
    create_test_user,
)
from authentik.enterprise.stages.account_lockdown.models import AccountLockdownStage
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.generators import generate_id

# Patch for enterprise license check
patch_license = patch(
    "authentik.enterprise.models.LicenseUsageStatus.is_valid",
    MagicMock(return_value=True),
)


@patch_license
class AccountLockdownAPITestCase(APITestCase):
    """Shared helpers for account lockdown API tests."""

    def setUp(self) -> None:
        self.lockdown_flow = create_test_flow(FlowDesignation.STAGE_CONFIGURATION)
        self.lockdown_stage = AccountLockdownStage.objects.create(name=generate_id())
        FlowStageBinding.objects.create(
            target=self.lockdown_flow,
            stage=self.lockdown_stage,
            order=0,
        )
        self.brand = create_test_brand()
        self.brand.flow_lockdown = self.lockdown_flow
        self.brand.save()

    def create_user_with_email(self):
        """Create a regular user with a unique email address."""
        user = create_test_user()
        user.email = f"{generate_id()}@test.com"
        user.save()
        return user

    def assert_redirect_targets(self, response, user):
        """Assert that a response contains a pre-planned lockdown flow link for a user."""
        self.assertEqual(response.status_code, 200)
        body = loads(response.content)
        self.assertIn(self.lockdown_flow.slug, body["link"])
        self.assertEqual(urlparse(body["link"]).query, "")
        plan = self.client.session[SESSION_KEY_PLAN]
        self.assertEqual(plan.context[PLAN_CONTEXT_PENDING_USER].pk, user.pk)

    def assert_no_flow_configured(self, response):
        """Assert that the API reports a missing lockdown flow."""
        self.assertEqual(response.status_code, 400)
        body = loads(response.content)
        self.assertIn("No lockdown flow configured", body["non_field_errors"][0])


@patch_license
class TestUsersAccountLockdownAPI(AccountLockdownAPITestCase):
    """Test Users Account Lockdown API"""

    def setUp(self) -> None:
        super().setUp()
        self.actor = create_test_user()
        self.user = self.create_user_with_email()

    def test_account_lockdown_with_change_user_returns_redirect(self):
        """Test that account lockdown allows users with change_user permission."""
        self.actor.assign_perms_to_managed_role("authentik_core.change_user", self.user)
        self.client.force_login(self.actor)

        response = self.client.post(
            reverse("authentik_api:user-account-lockdown"),
            data={"user": self.user.pk},
            format="json",
        )

        self.assert_redirect_targets(response, self.user)

    def test_account_lockdown_no_flow_configured(self):
        """Test account lockdown when no flow is configured"""
        self.brand.flow_lockdown = None
        self.brand.save()
        self.actor.assign_perms_to_managed_role("authentik_core.change_user", self.user)
        self.client.force_login(self.actor)

        response = self.client.post(
            reverse("authentik_api:user-account-lockdown"),
            data={"user": self.user.pk},
            format="json",
        )

        self.assert_no_flow_configured(response)

    def test_account_lockdown_unauthenticated(self):
        """Test account lockdown requires authentication"""
        response = self.client.post(
            reverse("authentik_api:user-account-lockdown"),
            data={"user": self.user.pk},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_account_lockdown_without_change_user_denied(self):
        """Test account lockdown denies users without change_user permission."""
        self.client.force_login(self.actor)

        response = self.client.post(
            reverse("authentik_api:user-account-lockdown"),
            data={"user": self.user.pk},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_account_lockdown_self_returns_redirect(self):
        """Test successful self-service account lockdown returns a direct redirect."""
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("authentik_api:user-account-lockdown"),
            data={},
            format="json",
        )

        self.assert_redirect_targets(response, self.user)

    def test_account_lockdown_self_target_without_change_user_returns_redirect(self):
        """Test self-service does not require change_user permission."""
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("authentik_api:user-account-lockdown"),
            data={"user": self.user.pk},
            format="json",
        )

        self.assert_redirect_targets(response, self.user)
