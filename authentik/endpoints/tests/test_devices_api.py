from datetime import datetime, timedelta

from django.urls import reverse
from django.utils.timezone import now
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user
from authentik.endpoints.models import Connector, Device, DeviceConnection
from authentik.lib.generators import generate_id
from authentik.providers.rac.models import Protocols, RACConnectionOverride


class TestDevicesAPI(APITestCase):
    def create_device_with_snapshot(self, t: datetime):
        device = Device.objects.create(
            identifier=generate_id(),
            name=generate_id(),
        )
        connector = Connector.objects.create(name=generate_id())
        connection = DeviceConnection.objects.create(
            device=device,
            connector=connector,
        )
        snap = connection.create_snapshot({"vendor": {"goauthentik.io/testing": {"foo": "bar"}}})
        snap.created = t
        snap.save()

    def test_summary(self):
        user = create_test_admin_user()
        self.client.force_login(user)
        self.create_device_with_snapshot(now())
        self.create_device_with_snapshot(now())
        res = self.client.get(reverse("authentik_api:endpoint_device-summary"))
        self.assertEqual(res.status_code, 200)
        self.assertJSONEqual(
            res.content, {"outdated_agent_count": 0, "total_count": 2, "unreachable_count": 0}
        )

    def test_summary_unreachable(self):
        user = create_test_admin_user()
        self.client.force_login(user)
        self.create_device_with_snapshot(now())
        self.create_device_with_snapshot(now())
        self.create_device_with_snapshot(now() - timedelta(hours=26))
        self.create_device_with_snapshot(now() - timedelta(hours=26))
        self.create_device_with_snapshot(now() - timedelta(hours=26))
        res = self.client.get(reverse("authentik_api:endpoint_device-summary"))
        self.assertEqual(res.status_code, 200)
        self.assertJSONEqual(
            res.content, {"outdated_agent_count": 0, "total_count": 5, "unreachable_count": 3}
        )

    def test_create(self):
        """Devices can be created by hand, for machines which are not enrolled
        through a connector"""
        user = create_test_admin_user()
        self.client.force_login(user)
        name = generate_id()
        res = self.client.post(
            reverse("authentik_api:endpoint_device-list"),
            data={
                "name": name,
                "rac": {"host": "host.example.com", "protocol": Protocols.SSH},
            },
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 201)
        device = Device.objects.get(name=name)
        self.assertTrue(device.identifier.startswith("manual://"))
        self.assertFalse(device.expiring)
        # A device which is added by hand has to say how it is reached
        self.assertEqual(device.rac_override.host, "host.example.com")
        self.assertEqual(device.rac_override.protocol, Protocols.SSH)

    def test_create_without_connection(self):
        """A device which is added by hand cannot report how it is reached, so it has
        to be told"""
        user = create_test_admin_user()
        self.client.force_login(user)
        res = self.client.post(
            reverse("authentik_api:endpoint_device-list"),
            data={"name": generate_id()},
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(set(res.json().keys()), {"rac"})

    def test_list_without_connection(self):
        """A device which is enrolled by a connector has no connection settings"""
        user = create_test_admin_user()
        self.client.force_login(user)
        device = Device.objects.create(identifier=generate_id(), name=generate_id())
        res = self.client.get(
            reverse("authentik_api:endpoint_device-detail", kwargs={"pk": device.device_uuid})
        )
        self.assertEqual(res.status_code, 200)
        self.assertIsNone(res.json()["rac"])

    def test_update(self):
        """A device which is enrolled reports how it is reached, so updating one does
        not require it"""
        user = create_test_admin_user()
        self.client.force_login(user)
        device = Device.objects.create(identifier=generate_id(), name=generate_id())
        name = generate_id()
        res = self.client.patch(
            reverse("authentik_api:endpoint_device-detail", kwargs={"pk": device.device_uuid}),
            data={"name": name},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        device.refresh_from_db()
        self.assertEqual(device.name, name)

    def test_update_connection(self):
        """How a device is reached can be changed after it was added"""
        user = create_test_admin_user()
        self.client.force_login(user)
        device = Device.objects.create(identifier=generate_id(), name=generate_id())
        RACConnectionOverride.objects.create(
            device=device, host="host.example.com", protocol=Protocols.SSH
        )
        res = self.client.patch(
            reverse("authentik_api:endpoint_device-detail", kwargs={"pk": device.device_uuid}),
            data={"rac": {"host": "other.example.com", "protocol": Protocols.RDP}},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        device.rac_override.refresh_from_db()
        self.assertEqual(device.rac_override.host, "other.example.com")
        self.assertEqual(device.rac_override.protocol, Protocols.RDP)
