from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.endpoints.connectors.agent.models import AgentConnector, DeviceToken, EnrollmentToken
from authentik.endpoints.models import Device, DeviceConnection
from authentik.lib.generators import generate_id


class TestAgentConnector(APITestCase):

    def setUp(self):
        self.connector = AgentConnector.objects.create(
            name=generate_id(),
        )
        self.token = EnrollmentToken.objects.create(name=generate_id(), connector=self.connector)
        self.device = Device.objects.create(
            identifier=generate_id(),
        )
        self.connection = DeviceConnection.objects.create(
            device=self.device,
            connector=self.connector,
        )
        self.device_token = DeviceToken.objects.create(
            device=self.connection,
            key=generate_id(),
        )

    def test_enroll(self):
        response = self.client.post(
            reverse("authentik_api:agentconnector-enroll"),
            data={"device_serial": generate_id(), "device_name": "bar"},
            HTTP_AUTHORIZATION=f"Bearer {self.token.key}",
        )
        self.assertEqual(response.status_code, 200, response.content)

    def test_config(self):
        response = self.client.get(
            reverse("authentik_api:agentconnector-agent-config"),
            HTTP_AUTHORIZATION=f"Bearer {self.device_token.key}",
        )
        self.assertEqual(response.status_code, 200)

    def test_check_in(self):
        response = self.client.post(
            reverse("authentik_api:agentconnector-check-in"),
            data={
                "disks": [],
                "hardware": {
                    "cpu_count": 10,
                    "cpu_name": "Apple M1 Pro",
                    "manufacturer": "Apple Inc.",
                    "memory_bytes": 34359738368,
                    "model": "MacBookPro18,1",
                    "serial": generate_id(),
                },
                "network": {
                    "firewall_enabled": True,
                    "hostname": "jens-mbp.lab.beryju.org",
                    "interfaces": [],
                },
                "os": {"arch": "arm64", "family": "mac_os", "name": "macOS", "version": "15.7.1"},
                "processes": [],
                "vendor": {"io.goauthentik.platform": {"agent_version": "0.23.0-dev-8521"}},
            },
            HTTP_AUTHORIZATION=f"Bearer {self.device_token.key}",
        )
        self.assertEqual(response.status_code, 204)
