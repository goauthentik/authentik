from json import loads

from requests_mock import Mocker
from rest_framework.test import APITestCase

from authentik.endpoints.facts import OSFamily
from authentik.endpoints.models import Device
from authentik.enterprise.endpoints.connectors.fleet.models import FleetConnector
from authentik.events.models import NotificationWebhookMapping
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import load_fixture

TEST_HOST_UBUNTU = loads(load_fixture("fixtures/host_ubuntu.json"))
TEST_HOST_FEDORA = loads(load_fixture("fixtures/host_fedora.json"))
TEST_HOST_MACOS = loads(load_fixture("fixtures/host_macos.json"))
TEST_HOST_WINDOWS = loads(load_fixture("fixtures/host_windows.json"))

TEST_HOST = {"hosts": [TEST_HOST_UBUNTU, TEST_HOST_MACOS, TEST_HOST_WINDOWS, TEST_HOST_FEDORA]}


class TestFleetConnector(APITestCase):
    def setUp(self):
        self.connector = FleetConnector.objects.create(
            name=generate_id(), url="http://localhost", token=generate_id()
        )

    def test_sync(self):
        controller = self.connector.controller(self.connector)
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
                    "name": "Ubuntu",
                    "family": "linux",
                    "version": "24.04.3 LTS",
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
        self.connector.headers_mapping = mapping
        self.connector.save()
        controller = self.connector.controller(self.connector)
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

    def test_map_host_linux(self):
        controller = self.connector.controller(self.connector)
        self.assertEqual(
            controller.map_os(TEST_HOST_UBUNTU),
            {
                "arch": "x86_64",
                "family": OSFamily.linux,
                "name": "Ubuntu",
                "version": "24.04.3 LTS",
            },
        )
        self.assertEqual(
            controller.map_os(TEST_HOST_FEDORA),
            {
                "arch": "x86_64",
                "family": OSFamily.linux,
                "name": "Fedora Linux",
                "version": "43.0.0",
            },
        )

    def test_map_host_windows(self):
        controller = self.connector.controller(self.connector)
        self.assertEqual(
            controller.map_os(TEST_HOST_WINDOWS),
            {
                "arch": "x86_64",
                "family": OSFamily.windows,
                "name": "Windows Server 2022 Datacenter 21H2",
                "version": "10.0.20348.4405",
            },
        )

    def test_map_host_macos(self):
        controller = self.connector.controller(self.connector)
        self.assertEqual(
            controller.map_os(TEST_HOST_MACOS),
            {
                "arch": "arm64e",
                "family": OSFamily.macOS,
                "name": "macOS",
                "version": "26.0.1",
            },
        )
