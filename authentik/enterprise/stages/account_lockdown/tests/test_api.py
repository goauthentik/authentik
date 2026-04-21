"""Test Users Account Lockdown API"""

from json import loads
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import (
    create_test_admin_user,
    create_test_brand,
    create_test_flow,
    create_test_user,
)
from authentik.enterprise.stages.account_lockdown.stage import QS_LOCKDOWN_USER
from authentik.flows.models import FlowDesignation
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
        self.brand = create_test_brand()
        self.brand.flow_lockdown = self.lockdown_flow
        self.brand.save()

    def create_user_with_email(self):
        """Create a regular user with a unique email address."""
        user = create_test_user()
        user.email = f"{generate_id()}@test.com"
        user.save()
        return user

    def assert_flow_url_targets(self, response, user):
        """Assert that a response contains the lockdown flow URL for a user."""
        self.assertEqual(response.status_code, 200)
        body = loads(response.content)
        self.assertIn("flow_url", body)
        self.assertIn(self.lockdown_flow.slug, body["flow_url"])
        target_uuid = parse_qs(urlparse(body["flow_url"]).query).get(QS_LOCKDOWN_USER, [None])[0]
        self.assertEqual(target_uuid, str(user.pk))


@patch_license
class TestUsersAccountLockdownAPI(AccountLockdownAPITestCase):
    """Test Users Account Lockdown API"""

    def setUp(self) -> None:
        super().setUp()
        self.admin = create_test_admin_user()
        self.user = self.create_user_with_email()

    def test_account_lockdown_returns_flow_url(self):
        """Test that account lockdown returns a flow URL"""
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("authentik_api:user-account-lockdown"),
            data={"user": self.user.pk},
            format="json",
        )

        self.assert_flow_url_targets(response, self.user)

    def test_account_lockdown_no_flow_configured(self):
        """Test account lockdown when no flow is configured"""
        self.brand.flow_lockdown = None
        self.brand.save()
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("authentik_api:user-account-lockdown"),
            data={"user": self.user.pk},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        body = loads(response.content)
        self.assertIn("No lockdown flow configured", body["non_field_errors"][0])

    def test_account_lockdown_unauthenticated(self):
        """Test account lockdown requires authentication"""
        response = self.client.post(
            reverse("authentik_api:user-account-lockdown"),
            data={"user": self.user.pk},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_account_lockdown_non_admin(self):
        """Test account lockdown requires admin permissions"""
        regular_user = create_test_user()
        self.client.force_login(regular_user)

        response = self.client.post(
            reverse("authentik_api:user-account-lockdown"),
            data={"user": self.user.pk},
            format="json",
        )

        self.assertEqual(response.status_code, 403)


@patch_license
class TestUsersAccountLockdownSelfServiceAPI(AccountLockdownAPITestCase):
    """Test Users Account Lockdown Self-Service API - Flow-based approach"""

    def setUp(self) -> None:
        super().setUp()
        self.user = self.create_user_with_email()

    def test_account_lockdown_self_returns_flow_url(self):
        """Test successful self-service account lockdown returns a direct flow URL."""
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("authentik_api:user-account-lockdown"),
            data={},
            format="json",
        )

        self.assert_flow_url_targets(response, self.user)

    def test_account_lockdown_self_no_flow_configured(self):
        """Test self-service lockdown when no flow is configured"""
        self.brand.flow_lockdown = None
        self.brand.save()
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("authentik_api:user-account-lockdown"),
            data={},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        body = loads(response.content)
        self.assertIn("No lockdown flow configured", body["non_field_errors"][0])

    def test_account_lockdown_self_unauthenticated(self):
        """Test self-service lockdown requires authentication"""
        response = self.client.post(
            reverse("authentik_api:user-account-lockdown"),
            data={},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
