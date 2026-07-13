from asyncio import run
from dataclasses import asdict
from typing import Any

from msgraph.generated.models.managed_device import ManagedDevice
from msgraph.graph_service_client import GraphServiceClient

from authentik.endpoints.controller import BaseController, Capabilities
from authentik.endpoints.models import Device, DeviceConnection
from authentik.enterprise.endpoints.connectors.microsoft_intune.models import (
    MicrosoftIntuneConnector,
)
from authentik.policies.utils import delete_none_values


class MicrosoftIntuneController(BaseController):

    def __init__(self, connector: MicrosoftIntuneConnector):
        super().__init__(connector)
        self.credentials = connector.microsoft_credentials()

    @staticmethod
    def vendor_identifier() -> str:
        return "intune.microsoft.com"

    def capabilities(self) -> list[Capabilities]:
        return [Capabilities.ENROLL_AUTOMATIC_API]

    def client(self):
        return GraphServiceClient(**self.credentials)

    def sync_endpoints(self):
        client = self.client()
        devices = run(client.device_management.managed_devices.get())
        next_link = True
        while next_link:
            for dev in devices.value:
                serial = dev.serial_number or dev.id
                device, _ = Device.objects.get_or_create(
                    identifier=serial, defaults={"name": dev.device_name, "expiring": False}
                )
                connection, _ = DeviceConnection.objects.update_or_create(
                    device=device,
                    connector=self.connector,
                )
                connection.create_snapshot(self.map_device_data(dev))
            next_link = devices.odata_next_link
            if not next_link:
                break
            devices = run(client.device_management.managed_devices.with_url(next_link).get())

    def map_device_data(self, device: ManagedDevice) -> dict[str, Any]:
        return {
            "os": delete_none_values(
                {
                    "version": device.os_version,
                    "name": device.operating_system,
                }
            ),
            "disks": [],
            "network": delete_none_values({"hostname": device.device_name, "interfaces": []}),
            "hardware": delete_none_values(
                {
                    "model": device.model,
                    "manufacturer": device.manufacturer,
                    "serial": device.serial_number,
                    "memory_bytes": device.physical_memory_in_bytes,
                }
            ),
            "software": [],
            "vendor": {
                self.vendor_identifier(): asdict(device),
            },
        }
