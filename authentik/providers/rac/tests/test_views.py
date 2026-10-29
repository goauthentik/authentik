"""RAC Views tests"""

from json import loads

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.endpoints.models import DeviceAccessGroup
from authentik.events.models import Event, EventAction
from authentik.lib.generators import generate_id
from authentik.policies.denied import AccessDeniedResponse
from authentik.policies.dummy.models import DummyPolicy
from authentik.policies.models import PolicyBinding
from authentik.providers.rac.models import ConnectionToken, Protocols, RACProvider
from authentik.providers.rac.tests import create_test_device


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
        self.device = create_test_device(host=f"{generate_id()}:1324")

    def start_url(self, device=None, protocol=Protocols.RDP) -> str:
        return reverse(
            "authentik_providers_rac:start",
            kwargs={
                "app": self.app.slug,
                "device": str((device or self.device).pk),
                "protocol": protocol,
            },
        )

    def test_no_policy(self):
        """Test request"""
        self.client.force_login(self.user)
        response = self.client.get(self.start_url())
        self.assertEqual(response.status_code, 302)
        flow_response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )
        body = loads(flow_response.content)
        next_url = body["to"]
        final_response = self.client.get(next_url)
        self.assertEqual(final_response.status_code, 200)

    def test_authorized_once(self):
        """A launch authorizes a single connection, and requesting the challenge again
        does not add another one to the audit log"""
        self.client.force_login(self.user)
        Event.objects.all().delete()
        self.assertEqual(self.client.get(self.start_url()).status_code, 302)
        executor = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})

        self.assertIn("to", loads(self.client.get(executor).content))
        self.client.get(executor)

        self.assertEqual(ConnectionToken.objects.filter(device=self.device).count(), 1)
        self.assertEqual(
            list(
                Event.objects.filter(
                    action__in=[EventAction.LOGIN, EventAction.AUTHORIZE_APPLICATION]
                ).values_list("action", flat=True)
            ),
            [EventAction.AUTHORIZE_APPLICATION],
        )

    def test_app_deny(self):
        """Test request (deny on app level)"""
        PolicyBinding.objects.create(
            target=self.app,
            policy=DummyPolicy.objects.create(name="deny", result=False, wait_min=1, wait_max=2),
            order=0,
        )
        self.client.force_login(self.user)
        response = self.client.get(self.start_url())
        self.assertIsInstance(response, AccessDeniedResponse)

    def test_device_deny(self):
        """Test request (deny on device level)"""
        PolicyBinding.objects.create(
            target=self.device,
            policy=DummyPolicy.objects.create(name="deny", result=False, wait_min=1, wait_max=2),
            order=0,
        )
        self.client.force_login(self.user)
        response = self.client.get(self.start_url())
        self.assertEqual(response.status_code, 302)
        flow_response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )
        body = loads(flow_response.content)
        self.assertEqual(body["component"], "ak-stage-access-denied")

    def test_different_session(self):
        """Test request"""
        self.client.force_login(self.user)
        response = self.client.get(self.start_url())
        self.assertEqual(response.status_code, 302)
        flow_response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )
        body = loads(flow_response.content)
        next_url = body["to"]
        self.client.logout()
        final_response = self.client.get(next_url)
        self.assertEqual(final_response.url, reverse("authentik_core:if-user"))

    def test_protocol_not_available(self):
        """A device can only be connected to with a protocol it accepts"""
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.start_url(protocol=Protocols.SSH)).status_code, 404)

    def test_device_outside_access_group(self):
        """A provider limited to an access group must not reach devices outside it"""
        self.provider.access_group = DeviceAccessGroup.objects.create(name=generate_id())
        self.provider.save()
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.start_url()).status_code, 404)

        in_group = create_test_device(host=generate_id(), access_group=self.provider.access_group)
        self.assertEqual(self.client.get(self.start_url(in_group)).status_code, 302)
