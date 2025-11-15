from django.db.models import TextChoices
from rest_framework.serializers import (
    BooleanField,
    CharField,
    ChoiceField,
    FloatField,
    IntegerField,
    ListField,
    Serializer,
)

from authentik.core.api.utils import JSONDictField


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
    label = CharField(required=False, allow_blank=True)
    capacity_total = FloatField(required=False)
    capacity_used = FloatField(required=False)
    encryption = BooleanField(default=False, required=False)


class OperatingSystemSerializer(Serializer):
    family = ChoiceField(OSFamily.choices, required=True)
    name = CharField(required=False)
    version = CharField(required=False)
    arch = CharField(required=True)


class NetworkInterfaceSerializer(Serializer):
    name = CharField(required=True)
    hardware_address = CharField(required=True)
    # TODO: allow multiple IPs per interface
    ip_address = CharField(required=False)
    netmask = CharField(required=False)
    gateway = CharField(required=False)
    dns_servers = ListField(child=CharField(), allow_empty=True)


class NetworkSerializer(Serializer):
    hostname = CharField()
    firewall_enabled = BooleanField()
    interfaces = ListField(child=NetworkInterfaceSerializer(), allow_empty=True)


class HardwareSerializer(Serializer):
    model = CharField()
    manufacturer = CharField()
    serial = CharField()


class SoftwareSerializer(Serializer):
    name = CharField(required=True)
    version = CharField()
    # Package manager/source for this software installation
    source = CharField(required=True)


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
    vendor = JSONDictField()
