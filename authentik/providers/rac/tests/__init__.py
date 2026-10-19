"""RAC test helpers"""

from typing import Any
from uuid import uuid4

from authentik.endpoints.models import Connector, Device, DeviceConnection
from authentik.lib.generators import generate_id
from authentik.providers.rac.models import Protocols, RACConnectionOverride


def create_test_device(
    name: str | None = None,
    host: str | None = None,
    protocol: str = Protocols.RDP,
    **kwargs,
) -> Device:
    """Create a device, with a connection override when a host is given"""
    device = Device.objects.create(
        name=name or generate_id(),
        identifier=f"rac://{uuid4()}",
        expiring=False,
        **kwargs,
    )
    if host:
        RACConnectionOverride.objects.create(device=device, host=host, protocol=protocol)
    return device


def set_device_facts(device: Device, facts: dict[str, Any]) -> Device:
    """Report facts for a device, as a connector would"""
    connection = DeviceConnection.objects.create(
        device=device,
        connector=Connector.objects.create(name=generate_id()),
    )
    connection.create_snapshot(facts)
    return device
