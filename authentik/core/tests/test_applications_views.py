"""Test Applications API"""
from unittest.mock import MagicMock, patch

from django.urls import reverse

from authentik.brands.models import Brand
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_brand, create_test_flow
from authentik.flows.tests import FlowTestCase


class TestApplicationsViews(FlowTestCase):
    """Test applications Views"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()
        self.allowed = Application.objects.create(
            name="allowed", slug="allowed", meta_launch_url="https://goauthentik.io/%(username)s"
        )

    def test_check_redirect(self):
        """Test redirect"""
        empty_flow = create_test_flow()
        brand: Brand = create_test_brand()
        brand.flow_authentication = empty_flow
        brand.save()
        response = self.client.get(
            reverse(
                "authentik_core:application-launch",
                kwargs={"application_slug": self.allowed.slug},
            ),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        with patch(
            "authentik.flows.stage.StageView.get_pending_user", MagicMock(return_value=self.user)
        ):
            response = self.client.post(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": empty_flow.slug})
            )
            self.assertEqual(response.status_code, 200)
            self.assertStageRedirects(response, f"https://goauthentik.io/{self.user.username}")

    def test_check_redirect_auth(self):
        """Test redirect"""
        self.client.force_login(self.user)
        empty_flow = create_test_flow()
        brand: Brand = create_test_brand()
        brand.flow_authentication = empty_flow
        brand.save()
        response = self.client.get(
            reverse(
                "authentik_core:application-launch",
                kwargs={"application_slug": self.allowed.slug},
            ),
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"https://goauthentik.io/{self.user.username}")
