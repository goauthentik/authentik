from rest_framework.test import APITestCase

from authentik.endpoints.models import Connector, Device, DeviceConnection
from authentik.lib.generators import generate_id


class TestEndpointFacts(APITestCase):

    def test_facts_cache_purge(self):
        """Test that creating a snapshot for a new connection purges the facts cache"""
        device = Device.objects.create(
            identifier=generate_id(),
            name=generate_id(),
        )
        self.assertEqual(device.cached_facts.data, {})
        connector = Connector.objects.create(name=generate_id())
        connection = DeviceConnection.objects.create(
            device=device,
            connector=connector,
        )
        connection.create_snapshot({"vendor": {"goauthentik.io/testing": {"foo": "bar"}}})
        self.assertEqual(
            device.cached_facts.data, {"vendor": {"goauthentik.io/testing": {"foo": "bar"}}}
        )

    def test_facts_merge(self):
        """test facts merging"""
        device = Device.objects.create(
            identifier=generate_id(),
            name=generate_id(),
        )
        connection_a = DeviceConnection.objects.create(
            device=device,
            connector=Connector.objects.create(name=generate_id()),
        )
        connection_a.create_snapshot(
            {
                "software": [
                    {
                        "name": "software-a",
                        "version": "1.2.3.4",
                        "source": "package",
                    }
                ]
            }
        )

        connection_a = DeviceConnection.objects.create(
            device=device,
            connector=Connector.objects.create(name=generate_id()),
        )
        connection_a.create_snapshot(
            {
                "software": [
                    {
                        "name": "software-b",
                        "version": "5.6.7.8",
                        "source": "package",
                    }
                ]
            }
        )
        self.assertEqual(
            device.cached_facts.data,
            {
                "software": [
                    {
                        "name": "software-a",
                        "version": "1.2.3.4",
                        "source": "package",
                    },
                    {
                        "name": "software-b",
                        "version": "5.6.7.8",
                        "source": "package",
                    },
                ]
            },
        )
