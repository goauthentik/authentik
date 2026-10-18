from django.test import TestCase

from authentik.endpoints.models import Device
from authentik.lib.generators import generate_id


class TestDevice(TestCase):

    def test_get_or_create_conflict(self):
        """Identifier match wins when name matches a different device"""
        by_id = Device.objects.create(identifier=generate_id(), name=generate_id())
        by_name = Device.objects.create(identifier=generate_id(), name=generate_id())
        self.assertEqual(Device.get_or_create(by_id.identifier, by_name.name), by_id)
        self.assertEqual(Device.get_or_create(generate_id(), by_name.name), by_name)
