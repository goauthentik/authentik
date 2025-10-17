from typing import TYPE_CHECKING
from uuid import uuid4

from deepmerge import always_merger
from django.db import models
from django.utils.functional import cached_property
from model_utils.managers import InheritanceManager
from rest_framework.serializers import Serializer

from authentik.core.models import User
from authentik.endpoints.common_data import CommonDeviceDataSerializer
from authentik.flows.models import Stage
from authentik.flows.stage import StageView
from authentik.lib.models import InheritanceForeignKey, SerializerModel
from authentik.policies.models import PolicyBindingModel

if TYPE_CHECKING:
    from authentik.endpoints.connector import BaseConnector


class Device(SerializerModel):
    device_uuid = models.UUIDField(default=uuid4, primary_key=True)

    name = models.TextField()
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
    is_primary = models.BooleanField(default=False)


class DeviceConnection(SerializerModel):
    device_connection_uuid = models.UUIDField(default=uuid4, primary_key=True)
    device = models.ForeignKey("Device", on_delete=models.CASCADE)
    connector = models.ForeignKey("Connector", on_delete=models.CASCADE)
    data = models.JSONField(default=dict)


class Connector(SerializerModel):
    connector_uuid = models.UUIDField(default=uuid4, primary_key=True)

    name = models.TextField()

    objects = InheritanceManager()

    @property
    def stage(self) -> type[StageView] | None:
        return None

    @property
    def component(self) -> str:
        raise NotImplementedError

    @property
    def controller(self) -> type["BaseConnector[Connector]"]:
        raise NotImplementedError


class DeviceGroup(PolicyBindingModel):

    name = models.TextField(unique=True)


class EndpointStage(Stage):

    connector = InheritanceForeignKey(Connector, on_delete=models.CASCADE)

    @property
    def view(self) -> type["StageView"]:
        from authentik.endpoints.stage import EndpointStageView

        return EndpointStageView

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.endpoints.api.stages import EndpointStageSerializer

        return EndpointStageSerializer

    @property
    def component(self) -> str:
        return "ak-endpoints-stage"
