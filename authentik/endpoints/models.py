from uuid import uuid4

from deepmerge import always_merger
from django.db import models
from django.utils.functional import cached_property

from authentik.core.models import User
from authentik.endpoints.common_data import CommonDeviceDataSerializer
from authentik.lib.models import SerializerModel
from authentik.policies.models import PolicyBindingModel


class Device(SerializerModel):
    device_uuid = models.UUIDField(default=uuid4, primary_key=True)

    identifier = models.TextField(unique=True)
    users = models.ManyToManyField(User, through="DeviceUser")
    connections = models.ManyToManyField("Connector", through="DeviceConnection")
    group = models.ForeignKey("DeviceGroup", null=True, on_delete=models.SET_DEFAULT, default=None)

    @cached_property
    def data(self) -> CommonDeviceDataSerializer:
        data = {}
        for _data in self.deviceconnection_set.all().values_list("data", flat=True):
            always_merger.merge(data, _data)
        return data


class DeviceUser(SerializerModel):
    device_user_uuid = models.UUIDField(default=uuid4, primary_key=True)
    device = models.ForeignKey("Device", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_primary = models.BooleanField()


class DeviceConnection(SerializerModel):
    device_connection_uuid = models.UUIDField(default=uuid4, primary_key=True)
    device = models.ForeignKey("Device", on_delete=models.CASCADE)
    connector = models.ForeignKey("Connector", on_delete=models.CASCADE)
    data = models.JSONField(default=dict)


class Connector(SerializerModel):
    connector_uuid = models.UUIDField(default=uuid4, primary_key=True)

    name = models.TextField()


class DeviceGroup(PolicyBindingModel):

    name = models.TextField(unique=True)
