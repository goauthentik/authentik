from datetime import timedelta

from django.urls import reverse
from django.utils.timezone import now
from rest_framework.test import APITestCase

from authentik.blueprints.tests import reconcile_app
from authentik.core.tests.utils import create_test_admin_user
from authentik.endpoints.connectors.agent.api.connectors import AgentDeviceConnection
from authentik.endpoints.connectors.agent.models import AgentConnector, DeviceToken, EnrollmentToken
from authentik.endpoints.facts import OSFamily
from authentik.endpoints.models import Device, DeviceTag
from authentik.lib.generators import generate_id

CHECK_IN_DATA_VALID = {
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
}


class TestAgentAPI(APITestCase):

    def setUp(self):
        self.connector = AgentConnector.objects.create(name=generate_id())
        self.token = EnrollmentToken.objects.create(name=generate_id(), connector=self.connector)
        self.device = Device.objects.create(
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

    def test_enroll(self):
        response = self.client.post(
            reverse("authentik_api:agentconnector-enroll"),
            data={"device_serial": generate_id(), "device_name": "bar"},
            HTTP_AUTHORIZATION=f"Bearer {self.token.key}",
        )
        self.assertEqual(response.status_code, 200)

    def test_enroll_group(self):
        device_tag = DeviceTag.objects.create(name=generate_id())
        self.token.device_tags.add(device_tag)
        self.token.save()
        ident = generate_id()
        response = self.client.post(
            reverse("authentik_api:agentconnector-enroll"),
            data={"device_serial": ident, "device_name": "bar"},
            HTTP_AUTHORIZATION=f"Bearer {self.token.key}",
        )
        self.assertEqual(response.status_code, 200)
        device = Device.objects.filter(identifier=ident).first()
        self.assertIsNotNone(device)
        self.assertTrue(device.tags.contains(device_tag))

    def test_enroll_expired(self):
        dev_id = generate_id()
        self.token.expiring = True
        self.token.expires = now() - timedelta(hours=1)
        self.token.save()
        response = self.client.post(
            reverse("authentik_api:agentconnector-enroll"),
            data={"device_serial": dev_id, "device_name": "bar"},
            HTTP_AUTHORIZATION=f"Bearer {self.token.key}",
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Device.objects.filter(identifier=dev_id).exists())

    @reconcile_app("authentik_crypto")
    def test_config(self):
        response = self.client.get(
            reverse("authentik_api:agentconnector-agent-config"),
            HTTP_AUTHORIZATION=f"Bearer {self.device_token.key}",
        )
        self.assertEqual(response.status_code, 200)

    def test_check_in(self):
        response = self.client.post(
            reverse("authentik_api:agentconnector-check-in"),
            data=CHECK_IN_DATA_VALID,
            HTTP_AUTHORIZATION=f"Bearer {self.device_token.key}",
        )
        self.assertEqual(response.status_code, 204)

    def test_check_in_token_expired(self):
        self.device_token.expiring = True
        self.device_token.expires = now() - timedelta(hours=1)
        self.device_token.save()
        response = self.client.post(
            reverse("authentik_api:agentconnector-check-in"),
            data=CHECK_IN_DATA_VALID,
            HTTP_AUTHORIZATION=f"Bearer {self.device_token.key}",
        )
        self.assertEqual(response.status_code, 403)

    def test_check_in_device_expired(self):
        self.device.expiring = True
        self.device.expires = now() - timedelta(hours=1)
        self.device.save()
        response = self.client.post(
            reverse("authentik_api:agentconnector-check-in"),
            data=CHECK_IN_DATA_VALID,
            HTTP_AUTHORIZATION=f"Bearer {self.device_token.key}",
        )
        self.assertEqual(response.status_code, 403)

    def test_mdm_api_wrong_platform(self):
        self.client.force_login(create_test_admin_user())
        res = self.client.post(
            reverse(
                "authentik_api:agentconnector-mdm-config",
                kwargs={
                    "pk": self.connector.pk,
                },
            ),
            data={"platform": OSFamily.android, "enrollment_token": self.token.pk},
        )
        self.assertEqual(res.status_code, 400)
        self.assertJSONEqual(res.content, {"platform": ["Selected platform not supported"]})

    def test_mdm_api_wrong_token(self):
        self.client.force_login(create_test_admin_user())
        other_connector = AgentConnector.objects.create(name=generate_id())
        self.token.connector = other_connector
        self.token.save()
        res = self.client.post(
            reverse(
                "authentik_api:agentconnector-mdm-config",
                kwargs={
                    "pk": self.connector.pk,
                },
            ),
            data={"platform": OSFamily.macOS, "enrollment_token": self.token.pk},
        )
        self.assertEqual(res.status_code, 400)
        self.assertJSONEqual(res.content, {"enrollment_token": ["Invalid token for connector"]})

    def test_mdm_api_expired_token(self):
        self.client.force_login(create_test_admin_user())
        self.token.expires = now() - timedelta(hours=1)
        self.token.save()
        res = self.client.post(
            reverse(
                "authentik_api:agentconnector-mdm-config",
                kwargs={
                    "pk": self.connector.pk,
                },
            ),
            data={"platform": OSFamily.macOS, "enrollment_token": self.token.pk},
        )
        self.assertEqual(res.status_code, 400)
        self.assertJSONEqual(res.content, {"enrollment_token": ["Token is expired"]})

    def test_mdm_api(self):
        self.client.force_login(create_test_admin_user())
        res = self.client.post(
            reverse(
                "authentik_api:agentconnector-mdm-config",
                kwargs={
                    "pk": self.connector.pk,
                },
            ),
            data={"platform": OSFamily.macOS, "enrollment_token": self.token.pk},
        )
        self.assertEqual(res.status_code, 200)
