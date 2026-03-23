from enum import StrEnum

from rest_framework.fields import SerializerMethodField

from authentik.core.api.utils import ModelSerializer
from authentik.endpoints.controller import MERGED_VENDOR
from authentik.endpoints.facts import DeviceFacts
from authentik.endpoints.models import Connector, DeviceFactSnapshot
from authentik.lib.utils.reflection import all_subclasses


def get_vendor_choices():
    choices = [(MERGED_VENDOR, MERGED_VENDOR)]
    for connector_type in all_subclasses(Connector):
        ident = connector_type().controller.vendor_identifier()
        choices.append((ident, ident))
    return choices


vendors = StrEnum("DeviceConnectorVendors", get_vendor_choices())


class DeviceFactSnapshotSerializer(ModelSerializer):

    data = DeviceFacts()
    vendor = SerializerMethodField()

    def get_vendor(self, instance: DeviceFactSnapshot) -> vendors:
        return self.context.get("vendor", MERGED_VENDOR)

    class Meta:
        model = DeviceFactSnapshot
        fields = [
            "data",
            "connection",
            "created",
            "expires",
            "vendor",
        ]
        extra_kwargs = {
            "created": {"read_only": True},
            "expires": {"read_only": True},
        }
