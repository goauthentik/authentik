from django.db.models import TextChoices
from drf_spectacular.extensions import OpenApiSerializerFieldExtension
from drf_spectacular.plumbing import build_basic_type
from drf_spectacular.types import OpenApiTypes
from rest_framework.serializers import (
    BooleanField,
    CharField,
    ChoiceField,
    IntegerField,
    ListField,
    Serializer,
)

from authentik.core.api.utils import JSONDictField


class BigIntegerFieldFix(OpenApiSerializerFieldExtension):

    target_class = "authentik.endpoints.facts.BigIntegerField"

    def map_serializer_field(self, auto_schema, direction):
        return build_basic_type(OpenApiTypes.INT64)


class BigIntegerField(IntegerField): ...


class OSFamily(TextChoices):
    linux = "linux"
    unix = "unix"
    bsd = "bsd"
    windows = "windows"
    macOS = "mac_os"
    android = "android"
    iOS = "i_os"
    other = "other"


class DiskSerializer(Serializer):
    name = CharField(required=True)
    mountpoint = CharField(required=True)
    label = CharField(required=False, allow_blank=True)
    capacity_total_bytes = BigIntegerField(required=False)
    capacity_used_bytes = BigIntegerField(required=False)
    encryption_enabled = BooleanField(default=False, required=False)


class OperatingSystemSerializer(Serializer):
    family = ChoiceField(OSFamily.choices, required=True)
    name = CharField(required=False)
    version = CharField(required=False)
    arch = CharField(required=True)


class NetworkInterfaceSerializer(Serializer):
    name = CharField(required=True)
    hardware_address = CharField(required=True)
    ip_addresses = ListField(child=CharField(), required=False)
    dns_servers = ListField(child=CharField(), required=False, allow_empty=True)


class NetworkSerializer(Serializer):
    hostname = CharField()
    firewall_enabled = BooleanField(required=False)
    interfaces = ListField(child=NetworkInterfaceSerializer(), allow_empty=True)
    gateway = CharField(required=False)


class HardwareSerializer(Serializer):
    model = CharField()
    manufacturer = CharField()
    serial = CharField(allow_blank=True)

    cpu_name = CharField(required=False)
    cpu_count = IntegerField(required=False)

    memory_bytes = BigIntegerField(required=False)


class SoftwareSerializer(Serializer):
    name = CharField(required=True)
    version = CharField(required=False, allow_blank=True)
    # Package manager/source for this software installation
    source = CharField(required=True)
    path = CharField(required=False)


class ProcessSerializer(Serializer):
    id = IntegerField(required=True)
    name = CharField()
    user = CharField(required=False)


class DeviceFacts(Serializer):
    os = OperatingSystemSerializer(required=False, allow_null=True)
    disks = ListField(child=DiskSerializer(), required=False, allow_null=True)
    network = NetworkSerializer(required=False, allow_null=True)
    hardware = HardwareSerializer(required=False, allow_null=True)
    software = ListField(child=SoftwareSerializer(), required=False, allow_null=True)
    processes = ListField(child=ProcessSerializer(), required=False, allow_null=True)
    vendor = JSONDictField(required=False)
