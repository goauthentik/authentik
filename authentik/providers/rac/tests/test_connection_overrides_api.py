"""Test RAC Connection overrides API"""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user
from authentik.endpoints.models import Device
from authentik.lib.generators import generate_id
from authentik.providers.rac.models import Protocols, RACConnectionOverride
from authentik.providers.rac.tests import create_test_device


class TestRACConnectionOverridesAPI(APITestCase):
    """Test connection overrides API"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def test_create_with_device(self):
        """An override for an enrolled device"""
        device = Device.objects.create(name=generate_id(), identifier=generate_id())
        response = self.client.post(
            reverse("authentik_api:racconnectionoverride-list"),
            data={
                "device": str(device.pk),
                "host": "host.example.com",
                "protocol": Protocols.SSH,
            },
        )
        self.assertEqual(response.status_code, 201)
        override = RACConnectionOverride.objects.get(device=device)
        self.assertEqual(override.host, "host.example.com")

    def test_create_device(self):
        """A device which is not enrolled is created along with its override"""
        name = generate_id()
        response = self.client.post(
            reverse("authentik_api:racconnectionoverride-list"),
            data={
                "device_name": name,
                "host": "host.example.com",
                "protocol": Protocols.RDP,
            },
        )
        self.assertEqual(response.status_code, 201)
        override = RACConnectionOverride.objects.get(pk=response.json()["pk"])
        self.assertEqual(override.device.name, name)
        self.assertFalse(override.device.expiring)
        self.assertTrue(override.device.identifier.startswith("rac://"))

    def test_create_requires_device(self):
        """Either a device or a name is required"""
        response = self.client.post(
            reverse("authentik_api:racconnectionoverride-list"),
            data={"host": "host.example.com", "protocol": Protocols.RDP},
        )
        self.assertEqual(response.status_code, 400)

    def test_create_requires_host_and_protocol(self):
        """Both the host and the protocol are required"""
        response = self.client.post(
            reverse("authentik_api:racconnectionoverride-list"),
            data={"device_name": generate_id()},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(set(response.json().keys()), {"host", "protocol"})

    def test_update_renames_device(self):
        """Updating the name renames the underlying device"""
        device = create_test_device(host=generate_id())
        name = generate_id()
        response = self.client.patch(
            reverse(
                "authentik_api:racconnectionoverride-detail",
                kwargs={"pk": device.rac_override.pk},
            ),
            data={"device_name": name, "host": "other.example.com"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        device.refresh_from_db()
        self.assertEqual(device.name, name)
        self.assertEqual(device.rac_override.host, "other.example.com")
