from typing import TYPE_CHECKING, Any
from uuid import uuid4

from deepmerge import always_merger
from django.db import models
from django.utils.functional import cached_property
from django.utils.timezone import now
from model_utils.managers import InheritanceManager
from rest_framework.serializers import Serializer

from authentik.core.models import ExpiringModel
from authentik.endpoints.facts import DeviceFacts
from authentik.flows.models import Stage
from authentik.flows.stage import StageView
from authentik.lib.models import InheritanceForeignKey, SerializerModel
from authentik.lib.utils.time import timedelta_from_string, timedelta_string_validator
from authentik.policies.models import PolicyBinding, PolicyBindingModel

if TYPE_CHECKING:
    from authentik.endpoints.connector import BaseConnector


class Device(PolicyBindingModel):
    device_uuid = models.UUIDField(default=uuid4, primary_key=True)

    name = models.TextField()
    identifier = models.TextField(unique=True)
    connections = models.ManyToManyField("Connector", through="DeviceConnection")
    group = models.ForeignKey("DeviceGroup", null=True, on_delete=models.SET_DEFAULT, default=None)

    @cached_property
    def data(self) -> DeviceFacts:
        data = {}
        for _data in self.deviceconnection_set.all().values_list("data", flat=True):
            always_merger.merge(data, _data)
        return data


class DeviceUserBinding(PolicyBinding):
    is_primary = models.BooleanField(default=False)


class DeviceConnection(SerializerModel):
    device_connection_uuid = models.UUIDField(default=uuid4, primary_key=True)
    device = models.ForeignKey("Device", on_delete=models.CASCADE)
    connector = models.ForeignKey("Connector", on_delete=models.CASCADE)

    def create_snapshot(self, data: dict[str, Any]):
        expires = now() + timedelta_from_string(self.connector.snapshot_expiry)
        DeviceFactSnapshot.objects.create(
            connection=self,
            data=data,
            expiring=True,
            expires=expires,
        )


class DeviceFactSnapshot(ExpiringModel):
    snapshot_id = models.UUIDField(primary_key=True, default=uuid4)
    connection = models.ForeignKey(DeviceConnection, on_delete=models.CASCADE)
    data = models.JSONField(default=dict)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Device fact snapshot {self.snapshot_id} from {self.created}"


class Connector(SerializerModel):
    connector_uuid = models.UUIDField(default=uuid4, primary_key=True)

    name = models.TextField()
    enabled = models.BooleanField()
    objects = InheritanceManager()

    snapshot_expiry = models.TextField(
        default="hours=24",
        validators=[timedelta_string_validator],
    )

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
