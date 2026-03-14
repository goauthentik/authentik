"""Test Users Account Lockdown API"""

from json import loads
from unittest.mock import MagicMock, patch

from django.urls import reverse
from guardian.shortcuts import assign_perm
from rest_framework.test import APITestCase

from authentik.brands.models import Brand
from authentik.core.tests.utils import create_test_admin_user, create_test_flow, create_test_user
from authentik.flows.models import FlowDesignation
from authentik.lib.generators import generate_id

# Patch for enterprise license check
patch_license = patch(
    "authentik.enterprise.models.LicenseUsageStatus.is_valid",
    MagicMock(return_value=True),
)


@patch_license
class TestUsersAccountLockdownAPI(APITestCase):
    """Test Users Account Lockdown API - Flow-based approach"""

    def setUp(self) -> None:
        self.admin = create_test_admin_user()
        self.user = create_test_user()
        self.user.email = f"{generate_id()}@test.com"
        self.user.save()
        # Create and configure lockdown flow on brand
        self.lockdown_flow = create_test_flow(FlowDesignation.STAGE_CONFIGURATION)
        self.brand = Brand.objects.first()
        self.brand.flow_lockdown = self.lockdown_flow
        self.brand.save()

    def test_account_lockdown_returns_flow_url(self):
        """Test that account lockdown returns a flow URL"""
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("authentik_api:user-account-lockdown"),
            data={"user": self.user.pk},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        body = loads(response.content)
        self.assertIn("flow_url", body)
        self.assertIn(self.lockdown_flow.slug, body["flow_url"])

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
class TestUsersAccountLockdownSelfServiceAPI(APITestCase):
    """Test Users Account Lockdown Self-Service API - Flow-based approach"""

    def setUp(self) -> None:
        self.user = create_test_user()
        self.user.email = f"{generate_id()}@test.com"
        self.user.save()
        # Create and configure lockdown flow on brand
        self.lockdown_flow = create_test_flow(FlowDesignation.STAGE_CONFIGURATION)
        self.brand = Brand.objects.first()
        self.brand.flow_lockdown = self.lockdown_flow
        self.brand.save()

    def test_account_lockdown_self_returns_flow_url(self):
        """Test successful self-service account lockdown returns flow URL"""
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("authentik_api:user-account-lockdown"),
            data={},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        body = loads(response.content)
        self.assertIn("flow_url", body)
        self.assertIn(self.lockdown_flow.slug, body["flow_url"])

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


@patch_license
class TestUsersAccountLockdownBulkAPI(APITestCase):
    """Test Users Account Lockdown Bulk API - Flow-based approach"""

    def setUp(self) -> None:
        self.admin = create_test_admin_user()
        self.user1 = create_test_user()
        self.user1.email = f"{generate_id()}@test.com"
        self.user1.save()
        self.user2 = create_test_user()
        self.user2.email = f"{generate_id()}@test.com"
        self.user2.save()
        # Create and configure lockdown flow on brand
        self.lockdown_flow = create_test_flow(FlowDesignation.STAGE_CONFIGURATION)
        self.brand = Brand.objects.first()
        self.brand.flow_lockdown = self.lockdown_flow
        self.brand.save()

    def test_account_lockdown_bulk_returns_flow_url(self):
        """Test successful bulk account lockdown returns flow URL"""
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("authentik_api:user-account-lockdown-bulk"),
            data={
                "users": [self.user1.pk, self.user2.pk],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        body = loads(response.content)
        self.assertIn("flow_url", body)
        self.assertIn(self.lockdown_flow.slug, body["flow_url"])

    def test_account_lockdown_bulk_no_flow_configured(self):
        """Test bulk lockdown when no flow is configured"""
        self.brand.flow_lockdown = None
        self.brand.save()
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("authentik_api:user-account-lockdown-bulk"),
            data={
                "users": [self.user1.pk],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        body = loads(response.content)
        self.assertIn("No lockdown flow configured", body["non_field_errors"][0])

    def test_account_lockdown_bulk_unauthenticated(self):
        """Test bulk lockdown requires authentication"""
        response = self.client.post(
            reverse("authentik_api:user-account-lockdown-bulk"),
            data={
                "users": [self.user1.pk],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_account_lockdown_bulk_object_permission_required(self):
        """Test bulk lockdown requires object-level permissions when not admin"""
        regular_user = create_test_user()
        assign_perm("authentik_core.change_user", regular_user, self.user1)
        self.client.force_login(regular_user)

        response = self.client.post(
            reverse("authentik_api:user-account-lockdown-bulk"),
            data={
                "users": [self.user1.pk, self.user2.pk],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)
