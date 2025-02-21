"""RAC Views tests"""

from json import loads

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.lib.generators import generate_id
from authentik.policies.denied import AccessDeniedResponse
from authentik.policies.dummy.models import DummyPolicy
from authentik.policies.models import PolicyBinding
from authentik.providers.rac.models import Endpoint, Protocols, RACProvider


class TestRACViews(APITestCase):
    """RAC Views tests"""

    def setUp(self):
        self.user = create_test_admin_user()
        self.flow = create_test_flow()
        self.provider = RACProvider.objects.create(name=generate_id(), authorization_flow=self.flow)
        self.app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
            provider=self.provider,
        )
        self.endpoint = Endpoint.objects.create(
            name=generate_id(),
            host=f"{generate_id()}:1324",
            protocol=Protocols.RDP,
            provider=self.provider,
        )

    def test_no_policy(self):
        """Test request"""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse(
                "authentik_providers_rac:start",
                kwargs={"app": self.app.slug, "endpoint": str(self.endpoint.pk)},
            )
        )
        self.assertEqual(response.status_code, 302)
        flow_response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )
        body = loads(flow_response.content)
        next_url = body["to"]
        final_response = self.client.get(next_url)
        self.assertEqual(final_response.status_code, 200)

    def test_app_deny(self):
        """Test request (deny on app level)"""
        PolicyBinding.objects.create(
            target=self.app,
            policy=DummyPolicy.objects.create(name="deny", result=False, wait_min=1, wait_max=2),
            order=0,
        )
        self.client.force_login(self.user)
        response = self.client.get(
            reverse(
                "authentik_providers_rac:start",
                kwargs={"app": self.app.slug, "endpoint": str(self.endpoint.pk)},
            )
        )
        self.assertIsInstance(response, AccessDeniedResponse)

    def test_endpoint_deny(self):
        """Test request (deny on endpoint level)"""
        PolicyBinding.objects.create(
            target=self.endpoint,
            policy=DummyPolicy.objects.create(name="deny", result=False, wait_min=1, wait_max=2),
            order=0,
        )
        self.client.force_login(self.user)
        response = self.client.get(
            reverse(
                "authentik_providers_rac:start",
                kwargs={"app": self.app.slug, "endpoint": str(self.endpoint.pk)},
            )
        )
        self.assertEqual(response.status_code, 302)
        flow_response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )
        body = loads(flow_response.content)
        self.assertEqual(body["component"], "ak-stage-access-denied")
