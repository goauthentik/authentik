from uuid import uuid4

from django.db import models
from django.utils.functional import cached_property

from authentik.core.models import User
from authentik.endpoints.common_data import CommonDeviceData
from authentik.lib.models import SerializerModel


class Device(SerializerModel):
    device_uuid = models.UUIDField(default=uuid4)

    identifier = models.TextField(unique=True)
    users = models.ManyToManyField(User, through="DeviceUser")
    connections = models.ManyToManyField("Connector", through="DeviceConnection")

    @cached_property
    def data(self) -> CommonDeviceData:
        pass


class DeviceUser(models.Model):
    device_user_uuid = models.UUIDField(default=uuid4)
    device = models.ForeignKey("Device", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_primary = models.BooleanField()


class DeviceConnection(models.Model):
    device_connection_uuid = models.UUIDField(default=uuid4)
    device = models.ForeignKey("Device", on_delete=models.CASCADE)
    connection = models.ForeignKey("Connector", on_delete=models.CASCADE)
    data = models.JSONField(default=dict)


class Connector(SerializerModel):
    connector_uuid = models.UUIDField(default=uuid4)

    name = models.TextField()
