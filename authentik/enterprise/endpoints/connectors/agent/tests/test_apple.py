from json import loads
from urllib.parse import quote

from django.test import TestCase
from django.urls import reverse

from authentik.core.tests.utils import create_test_user
from authentik.endpoints.connectors.agent.models import (
    AgentConnector,
    AgentDeviceConnection,
    AppleNonce,
    DeviceToken,
    EnrollmentToken,
)
from authentik.endpoints.models import Device
from authentik.lib.generators import generate_id


class TestAppleViews(TestCase):

    def setUp(self):
        self.connector = AgentConnector.objects.create(name=generate_id())
        self.token = EnrollmentToken.objects.create(name=generate_id(), connector=self.connector)
        self.device = Device.objects.create(
            name=generate_id(),
            identifier=generate_id(),
        )
        self.connection = AgentDeviceConnection.objects.create(
            device=self.device,
            connector=self.connector,
        )
        self.user = create_test_user()

    def test_apple_site_association(self):
        res = self.client.get(reverse("authentik_enterprise_endpoints_connectors_agent_root:asa"))
        self.assertEqual(res.status_code, 200)

    def test_apple_nonce(self):
        device_token = DeviceToken.objects.create(device=self.connection)
        res = self.client.post(
            reverse("authentik_enterprise_endpoints_connectors_agent:psso-nonce"),
            data={"x-ak-device-token": quote(device_token.key)},
        )
        self.assertEqual(res.status_code, 200)
        nonce = loads(res.content.decode()).get("Nonce")
        self.assertIsNotNone(nonce)
        db_nonce = AppleNonce.objects.filter(nonce=nonce).first()
        self.assertIsNotNone(db_nonce)
        self.assertFalse(db_nonce.is_expired)
