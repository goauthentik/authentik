from django.db.models import TextChoices
from rest_framework.serializers import BooleanField, CharField, ChoiceField, ListField, Serializer


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
    encryption = BooleanField()


class OperatingSystemSerializer(Serializer):
    firewall_enabled = BooleanField()
    family = ChoiceField(OSFamily.choices)
    name = CharField()
    version = CharField()


class NetworkSerializer(Serializer):
    hostname = CharField()
    dns_servers = ListField(child=CharField(), allow_empty=True)


class HardwareSerializer(Serializer):
    model = CharField()
    manufacturer = CharField()


class SoftwareSerializer(Serializer):
    name = CharField()
    version = CharField()


class CommonDeviceDataSerializer(Serializer):
    os = OperatingSystemSerializer(required=False, allow_null=True)
    disks = ListField(child=DiskSerializer(), required=False, allow_null=True)
    network = NetworkSerializer(required=False, allow_null=True)
    hardware = HardwareSerializer(required=False, allow_null=True)
    software = ListField(child=SoftwareSerializer(), required=False, allow_null=True)
