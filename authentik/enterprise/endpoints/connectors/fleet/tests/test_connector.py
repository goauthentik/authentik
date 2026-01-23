from json import loads

from requests_mock import Mocker
from rest_framework.test import APITestCase

from authentik.endpoints.models import Device
from authentik.enterprise.endpoints.connectors.fleet.models import FleetConnector
from authentik.events.models import NotificationWebhookMapping
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import load_fixture

TEST_HOST_UBUNTU = loads(load_fixture("fixtures/host_ubuntu.json"))
TEST_HOST_MACOS = loads(load_fixture("fixtures/host_macos.json"))
TEST_HOST_WINDOWS = loads(load_fixture("fixtures/host_windows.json"))

TEST_HOST = {"hosts": [TEST_HOST_UBUNTU, TEST_HOST_MACOS, TEST_HOST_WINDOWS]}


class TestFleetConnector(APITestCase):
    def test_sync(self):
        connector = FleetConnector.objects.create(
            name=generate_id(), url="http://localhost", token=generate_id()
        )
        controller = connector.controller(connector)
        with Mocker() as mock:
            mock.get(
                "http://localhost/api/v1/fleet/hosts?order_key=hardware_serial&page=0&per_page=50&device_mapping=true&populate_software=true&populate_users=true",
                json=TEST_HOST,
            )
            mock.get(
                "http://localhost/api/v1/fleet/hosts?order_key=hardware_serial&page=1&per_page=50&device_mapping=true&populate_software=true&populate_users=true",
                json={"hosts": []},
            )
            controller.sync_endpoints()
        device = Device.objects.filter(
            identifier="VMware-56 4d 4a 5a b0 22 7b d7-9b a5 0b dc 8f f2 3b 60"
        ).first()
        self.assertIsNotNone(device)
        self.assertEqual(
            device.cached_facts.data,
            {
                "os": {
                    "arch": "x86_64",
                    "name": "debian",
                    "family": "linux",
                    "version": "Ubuntu 24.04.3 LTS",
                },
                "disks": [],
                "vendor": {"fleetdm.com": {"policies": [], "agent_version": ""}},
                "network": {"hostname": "ubuntu-desktop", "interfaces": []},
                "hardware": {
                    "model": "VMware20,1",
                    "serial": "VMware-56 4d 4a 5a b0 22 7b d7-9b a5 0b dc 8f f2 3b 60",
                    "cpu_count": 2,
                    "cpu_name": "Intel(R) Core(TM) i5-10500T CPU @ 2.30GHz",
                    "manufacturer": "VMware, Inc.",
                    "memory_bytes": 2062721024,
                },
                "software": [],
            },
        )

    def test_sync_headers(self):
        mapping = NotificationWebhookMapping.objects.create(
            name=generate_id(), expression="""return {"foo": "bar"}"""
        )
        connector = FleetConnector.objects.create(
            name=generate_id(), url="http://localhost", token=generate_id(), headers_mapping=mapping
        )
        controller = connector.controller(connector)
        with Mocker() as mock:
            mock.get(
                "http://localhost/api/v1/fleet/hosts?order_key=hardware_serial&page=0&per_page=50&device_mapping=true&populate_software=true&populate_users=true",
                json=TEST_HOST,
            )
            mock.get(
                "http://localhost/api/v1/fleet/hosts?order_key=hardware_serial&page=1&per_page=50&device_mapping=true&populate_software=true&populate_users=true",
                json={"hosts": []},
            )
            controller.sync_endpoints()
        self.assertEqual(mock.call_count, 2)
        self.assertEqual(mock.request_history[0].method, "GET")
        self.assertEqual(mock.request_history[0].headers["foo"], "bar")
        self.assertEqual(mock.request_history[1].method, "GET")
        self.assertEqual(mock.request_history[1].headers["foo"], "bar")
