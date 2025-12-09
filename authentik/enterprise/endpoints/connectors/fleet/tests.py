from requests_mock import Mocker
from rest_framework.test import APITestCase

from authentik.endpoints.models import Device
from authentik.enterprise.endpoints.connectors.fleet.models import FleetConnector
from authentik.events.models import NotificationWebhookMapping
from authentik.lib.generators import generate_id

TEST_HOST = {
    "hosts": [
        {
            "created_at": "2025-09-20T17:46:17Z",
            "updated_at": "2025-12-05T17:13:24Z",
            "software": None,
            "software_updated_at": "2025-12-05T17:13:24Z",
            "id": 8,
            "detail_updated_at": "2025-12-05T17:13:25Z",
            "label_updated_at": "2025-12-05T17:13:25Z",
            "policy_updated_at": "2025-12-05T16:41:15Z",
            "last_enrolled_at": "2025-09-20T17:46:17Z",
            "seen_time": "2025-12-05T17:38:07Z",
            "refetch_requested": False,
            "hostname": "oci-kube-1",
            "uuid": "72a6f06a-d27d-45ec-996d-0ca298f50c61",
            "platform": "ubuntu",
            "osquery_version": "5.20.0",
            "orbit_version": None,
            "fleet_desktop_version": None,
            "scripts_enabled": None,
            "os_version": "Ubuntu 24.04.3 LTS",
            "build": "",
            "platform_like": "debian",
            "code_name": "noble",
            "uptime": 8454318000000000,
            "memory": 25141047296,
            "cpu_type": "aarch64",
            "cpu_subtype": "0",
            "cpu_brand": "",
            "cpu_physical_cores": 4,
            "cpu_logical_cores": 4,
            "hardware_vendor": "QEMU",
            "hardware_model": "KVM Virtual Machine",
            "hardware_version": "virt-4.2",
            "hardware_serial": "8A19B472-3FD7-475F-88F3-B2C2D0BC0D1A",
            "computer_name": "oci-kube-1",
            "public_ip": "130.61.116.187",
            "primary_ip": "10.120.90.154",
            "primary_mac": "02:00:17:01:d0:d2",
            "distributed_interval": 10,
            "config_tls_refresh": 60,
            "logger_tls_period": 10,
            "team_id": 2,
            "pack_stats": None,
            "team_name": "prod",
            "gigs_disk_space_available": 74.88,
            "percent_disk_space_available": 72,
            "gigs_total_disk_space": 103.86,
            "gigs_all_disk_space": 103.86,
            "issues": {
                "failing_policies_count": 0,
                "critical_vulnerabilities_count": 0,
                "total_issues_count": 0,
            },
            "device_mapping": None,
            "mdm": {
                "enrollment_status": None,
                "dep_profile_error": False,
                "server_url": None,
                "name": "",
                "encryption_key_available": False,
                "connected_to_fleet": False,
            },
            "refetch_critical_queries_until": None,
            "last_restarted_at": "2025-08-29T20:48:07Z",
            "status": "online",
            "display_text": "oci-kube-1",
            "display_name": "oci-kube-1",
        }
    ]
}


class TestFleetConnector(APITestCase):

    def test_sync(self):
        connector = FleetConnector.objects.create(
            name=generate_id(), url="http://localhost", token=generate_id()
        )
        controller = connector.controller(connector)
        with Mocker() as mock:
            mock.get(
                "http://localhost/api/v1/fleet/hosts?order_key=hardware_serial&page=1&per_page=50&device_mapping=true&populate_software=true&populate_users=true",
                json=TEST_HOST,
            )
            mock.get(
                "http://localhost/api/v1/fleet/hosts?order_key=hardware_serial&page=2&per_page=50&device_mapping=true&populate_software=true&populate_users=true",
                json={"hosts": []},
            )
            controller.sync_endpoints()
        device = Device.objects.filter(identifier="8A19B472-3FD7-475F-88F3-B2C2D0BC0D1A").first()
        self.assertIsNotNone(device)
        self.assertEqual(
            device.cached_facts.data,
            {
                "os": {
                    "arch": "aarch64",
                    "name": "debian",
                    "family": "linux",
                    "version": "Ubuntu 24.04.3 LTS",
                },
                "disks": [],
                "vendor": {"fleetdm.com": {"policies": [], "agent_version": ""}},
                "network": {"hostname": "oci-kube-1", "interfaces": []},
                "hardware": {
                    "model": "KVM Virtual Machine",
                    "serial": "8A19B472-3FD7-475F-88F3-B2C2D0BC0D1A",
                    "cpu_count": 4,
                    "manufacturer": "QEMU",
                    "memory_bytes": 25141047296,
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
                "http://localhost/api/v1/fleet/hosts?order_key=hardware_serial&page=1&per_page=50&device_mapping=true&populate_software=true&populate_users=true",
                json=TEST_HOST,
            )
            mock.get(
                "http://localhost/api/v1/fleet/hosts?order_key=hardware_serial&page=2&per_page=50&device_mapping=true&populate_software=true&populate_users=true",
                json={"hosts": []},
            )
            controller.sync_endpoints()
        self.assertEqual(mock.call_count, 2)
        self.assertEqual(mock.request_history[0].method, "GET")
        self.assertEqual(mock.request_history[0].headers["foo"], "bar")
        self.assertEqual(mock.request_history[1].method, "GET")
        self.assertEqual(mock.request_history[1].headers["foo"], "bar")
