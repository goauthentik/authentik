"""RAC test helpers"""

from typing import Any
from uuid import uuid4

from authentik.endpoints.models import Connector, Device, DeviceConnection
from authentik.lib.generators import generate_id
from authentik.providers.rac.models import RAC_ATTRIBUTES


def create_test_device(
    name: str | None = None,
    host: str | None = None,
    protocol: str | None = None,
    settings: dict[str, Any] | None = None,
    **kwargs,
) -> Device:
    """Create a device with RAC overrides set, as an admin would for a device that is
    not enrolled through a connector"""
    overrides = {}
    if host:
        overrides["host"] = host
    if protocol:
        overrides["protocol"] = protocol
    if settings:
        overrides["settings"] = settings
    overrides.update(kwargs.pop("overrides", {}))
    return Device.objects.create(
        name=name or generate_id(),
        identifier=f"rac://{uuid4()}",
        expiring=False,
        attributes={RAC_ATTRIBUTES: overrides} if overrides else {},
        **kwargs,
    )


def set_device_facts(device: Device, facts: dict[str, Any]) -> Device:
    """Report facts for a device, as a connector would"""
    connection = DeviceConnection.objects.create(
        device=device,
        connector=Connector.objects.create(name=generate_id()),
    )
    connection.create_snapshot(facts)
    return device
