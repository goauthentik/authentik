"""Test Applications API"""

from unittest.mock import MagicMock, patch

from django.urls import reverse

from authentik.brands.models import Brand
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_brand, create_test_flow
from authentik.flows.tests import FlowTestCase
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import OAuth2Provider


class TestApplicationsViews(FlowTestCase):
    """Test applications Views"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()
        self.app = Application.objects.create(
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
                kwargs={"application_slug": self.app.slug},
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
                kwargs={"application_slug": self.app.slug},
            ),
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"https://goauthentik.io/{self.user.username}")

    def test_redirect_application_auth_flow(self):
        """Test launching an application with a provider and an authentication flow set"""
        self.client.logout()
        auth_flow = create_test_flow()
        prov = OAuth2Provider.objects.create(
            name=generate_id(),
            authentication_flow=auth_flow,
        )
        self.app.provider = prov
        self.app.save()
        with self.assertFlowFinishes() as plan:
            response = self.client.get(
                reverse(
                    "authentik_core:application-launch",
                    kwargs={"application_slug": self.app.slug},
                ),
            )
            self.assertEqual(response.status_code, 302)
            self.assertEqual(
                response.url,
                reverse("authentik_core:if-flow", kwargs={"flow_slug": auth_flow.slug}),
            )
        plan = plan()
        self.assertEqual(len(plan.bindings), 1)
        self.assertTrue(plan.bindings[0].stage.is_in_memory)

    def test_redirect_application_no_auth(self):
        """Test launching an application with a provider and an authentication flow set"""
        self.client.logout()
        empty_flow = create_test_flow()
        brand: Brand = create_test_brand()
        brand.flow_authentication = empty_flow
        brand.save()

        prov = OAuth2Provider.objects.create(
            name=generate_id(),
        )
        self.app.provider = prov
        self.app.save()
        with self.assertFlowFinishes() as plan:
            response = self.client.get(
                reverse(
                    "authentik_core:application-launch",
                    kwargs={"application_slug": self.app.slug},
                ),
            )
            self.assertEqual(response.status_code, 302)
            self.assertEqual(
                response.url,
                reverse("authentik_core:if-flow", kwargs={"flow_slug": empty_flow.slug}),
            )
        plan = plan()
        self.assertEqual(len(plan.bindings), 1)
        self.assertTrue(plan.bindings[0].stage.is_in_memory)
