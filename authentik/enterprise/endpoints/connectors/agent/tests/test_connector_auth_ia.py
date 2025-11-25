from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.endpoints.connectors.agent.api.connectors import AgentDeviceConnection
from authentik.endpoints.connectors.agent.models import AgentConnector, DeviceToken, EnrollmentToken
from authentik.endpoints.models import Device
from authentik.lib.generators import generate_id


class TestConnectorAuthIA(APITestCase):

    def setUp(self):
        self.connector = AgentConnector.objects.create(
            name=generate_id(),
            domain_name=generate_id(),
        )
        self.token = EnrollmentToken.objects.create(name=generate_id(), connector=self.connector)
        self.device = Device.objects.create(
            name=generate_id(),
            identifier=generate_id(),
        )
        self.connection = AgentDeviceConnection.objects.create(
            device=self.device,
            connector=self.connector,
        )
        self.device_token = DeviceToken.objects.create(
            device=self.connection,
            key=generate_id(),
        )

    def test_auth_ia_initiate(self):
        response = self.client.post(
            reverse("authentik_api:agentconnector-auth-ia"),
            HTTP_AUTHORIZATION=f"Bearer {self.device_token.key}",
        )
        self.assertEqual(response.status_code, 200)
