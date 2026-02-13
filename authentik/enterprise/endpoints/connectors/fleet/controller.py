import re
from typing import Any

from django.db import transaction
from requests import RequestException
from rest_framework.exceptions import ValidationError

from authentik.core.models import User
from authentik.endpoints.controller import BaseController, ConnectorSyncException, EnrollmentMethods
from authentik.endpoints.facts import (
    DeviceFacts,
    OSFamily,
)
from authentik.endpoints.models import (
    Device,
    DeviceAccessGroup,
    DeviceConnection,
    DeviceUserBinding,
)
from authentik.enterprise.endpoints.connectors.fleet.models import FleetConnector as DBC
from authentik.events.utils import sanitize_item
from authentik.lib.utils.http import get_http_session
from authentik.policies.utils import delete_none_values


class FleetController(BaseController[DBC]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._session = get_http_session()
        self._session.headers["Authorization"] = f"Bearer {self.connector.token}"
        if self.connector.headers_mapping:
            self._session.headers.update(
                sanitize_item(
                    self.connector.headers_mapping.evaluate(
                        user=None,
                        request=None,
                        connector=self.connector,
                    )
                )
            )

    @staticmethod
    def vendor_identifier() -> str:
        return "fleetdm.com"

    def supported_enrollment_methods(self) -> list[EnrollmentMethods]:
        return [EnrollmentMethods.AUTOMATIC_API]

    def _url(self, path: str) -> str:
        return f"{self.connector.url}{path}"

    def _paginate_hosts(self):
        try:
            page = 0
            while True:
                self.logger.info("Fetching page of hosts...", page=page)
                res = self._session.get(
                    self._url("/api/v1/fleet/hosts"),
                    params={
                        "order_key": "hardware_serial",
                        "page": page,
                        "per_page": 50,
                        "device_mapping": "true",
                        "populate_software": "true",
                        "populate_users": "true",
                    },
                )
                res.raise_for_status()
                hosts: list[dict[str, Any]] = res.json()["hosts"]
                if len(hosts) < 1:
                    self.logger.info("No more hosts, finished")
                    break
                self.logger.info("Got hosts", count=len(hosts))
                yield from hosts
                page += 1
        except RequestException as exc:
            raise ConnectorSyncException(exc) from exc

    @transaction.atomic
    def sync_endpoints(self) -> None:
        for host in self._paginate_hosts():
            serial = host["hardware_serial"]
            device, _ = Device.objects.get_or_create(
                identifier=serial, defaults={"name": host["hostname"], "expiring": False}
            )
            connection, _ = DeviceConnection.objects.update_or_create(
                device=device,
                connector=self.connector,
            )
            if self.connector.map_users:
                self.map_users(host, device)
            if self.connector.map_teams_access_group:
                self.map_access_group(host, device)
            try:
                connection.create_snapshot(self.convert_host_data(host))
            except ValidationError as exc:
                self.logger.warning(
                    "failed to create snapshot for host", host=host["hostname"], exc=exc
                )

    def map_users(self, host: dict[str, Any], device: Device):
        for raw_user in host.get("device_mapping", []) or []:
            user = User.objects.filter(email=raw_user["email"]).first()
            if not user:
                continue
            DeviceUserBinding.objects.update_or_create(
                target=device,
                user=user,
                create_defaults={
                    "is_primary": True,
                    "order": 0,
                },
            )

    def map_access_group(self, host: dict[str, Any], device: Device):
        team_name = host.get("team_name")
        if not team_name:
            return
        group, _ = DeviceAccessGroup.objects.get_or_create(name=team_name)
        group.attributes["io.goauthentik.endpoints.connectors.fleet.team_id"] = host["team_id"]
        if device.access_group:
            return
        device.access_group = group
        device.save()

    @staticmethod
    def os_family(host: dict[str, Any]) -> OSFamily:
        if host["platform_like"] in ["debian", "rhel"]:
            return OSFamily.linux
        if host["platform_like"] == "windows":
            return OSFamily.windows
        if host["platform_like"] == "darwin":
            return OSFamily.macOS
        if host["platform"] == "android":
            return OSFamily.android
        if host["platform"] in ["ipados", "ios"]:
            return OSFamily.iOS
        return OSFamily.other

    def map_os(self, host: dict[str, Any]) -> dict[str, str]:
        family = FleetController.os_family(host)
        os = {
            "arch": self.or_none(host["cpu_type"]),
            "family": family,
            "name": self.or_none(host["platform_like"]),
            "version": self.or_none(host["os_version"]),
        }
        if not host["os_version"]:
            return delete_none_values(os)
        version = re.search(r"(\d+\.(?:\d+\.?)+)", host["os_version"])
        if not version:
            return delete_none_values(os)
        os["version"] = host["os_version"][version.start() :].strip()
        os["name"] = host["os_version"][0 : version.start()].strip()
        return delete_none_values(os)

    def or_none(self, value) -> Any | None:
        if value == "":
            return None
        return value

    def convert_host_data(self, host: dict[str, Any]) -> dict[str, Any]:
        """Convert host data from fleet to authentik"""
        fleet_version = ""
        for pkg in host.get("software") or []:
            if pkg["name"] in ["fleet-osquery", "fleet-desktop"]:
                fleet_version = pkg["version"]
        data = {
            "os": self.map_os(host),
            "disks": [],
            "network": delete_none_values(
                {"hostname": self.or_none(host["hostname"]), "interfaces": []}
            ),
            "hardware": delete_none_values(
                {
                    "model": self.or_none(host["hardware_model"]),
                    "manufacturer": self.or_none(host["hardware_vendor"]),
                    "serial": self.or_none(host["hardware_serial"]),
                    "cpu_name": self.or_none(host["cpu_brand"]),
                    "cpu_count": self.or_none(host["cpu_logical_cores"]),
                    "memory_bytes": self.or_none(host["memory"]),
                }
            ),
            "software": [
                delete_none_values(
                    {
                        "name": x["name"],
                        "version": x["version"],
                        "source": x["source"],
                    }
                )
                for x in (host.get("software") or [])
            ],
            "vendor": {
                "fleetdm.com": {
                    "policies": [
                        delete_none_values({"name": policy["name"], "status": policy["response"]})
                        for policy in host.get("policies", [])
                    ],
                    "agent_version": fleet_version,
                },
            },
        }
        facts = DeviceFacts(data=data)
        facts.is_valid(raise_exception=True)
        return facts.validated_data
