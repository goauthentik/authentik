from datetime import datetime, timedelta

from django.urls import reverse
from django.utils.timezone import now
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user
from authentik.endpoints.models import Connector, Device, DeviceConnection
from authentik.lib.generators import generate_id


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
