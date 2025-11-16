from typing import Any

from django.db import transaction
from requests import RequestException
from rest_framework.exceptions import ValidationError

from authentik.core.models import User
from authentik.endpoints.connector import BaseConnector, ConnectorSyncException, EnrollmentMethods
from authentik.endpoints.facts import (
    DeviceFacts,
    OSFamily,
)
from authentik.endpoints.models import (
    Device,
    DeviceConnection,
    DeviceUserBinding,
)
from authentik.enterprise.endpoints.connectors.fleet.models import FleetConnector as DBC
from authentik.lib.utils.http import get_http_session


class FleetConnector(BaseConnector[DBC]):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._session = get_http_session()
        self._session.headers["Authorization"] = f"Bearer {self.connector.token}"

    def supported_enrollment_methods(self) -> list[EnrollmentMethods]:
        return [EnrollmentMethods.AUTOMATIC_API]

    def _url(self, path: str) -> str:
        return f"{self.connector.url}{path}"

    def _paginate_hosts(self):
        try:
            page = 0
            while True:
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
                    break
                yield from hosts
                page += 1
        except RequestException as exc:
            raise ConnectorSyncException(exc) from exc

    @transaction.atomic
    def sync_endpoints(self) -> None:
        for host in self._paginate_hosts():
            serial = host["hardware_serial"]
            device, _ = Device.objects.get_or_create(identifier=serial)
            connection, _ = DeviceConnection.objects.update_or_create(
                device=device,
                connector=self.connector,
            )
            self.map_users(host, device)
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
                },
            )

    def convert_host_data(self, host: dict[str, Any]) -> dict[str, Any]:
        """Convert host data from fleet to authentik"""
        data = {
            "os": {
                "arch": host["cpu_type"],
                # TODO: mapping from fleet
                "family": OSFamily.linux,
                "name": host["platform_like"],
                "version": host["os_version"],
            },
            "disks": [],
            "network": {"hostname": host["hostname"], "interfaces": []},
            "hardware": {
                "model": host["hardware_model"],
                "manufacturer": host["hardware_vendor"],
                "serial": host["hardware_serial"],
            },
            "software": [
                {
                    "name": x["name"],
                    "version": x["version"],
                    "source": x["source"],
                }
                for x in host["software"]
            ],
            "vendor": {
                "fleetdm.com": {
                    "policies": [
                        {"name": policy["name"], "status": policy["response"]}
                        for policy in host.get("policies", [])
                    ]
                },
            },
        }
        facts = DeviceFacts(data=data)
        facts.is_valid(raise_exception=True)
        return facts.validated_data
