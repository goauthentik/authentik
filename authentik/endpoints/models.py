from typing import TYPE_CHECKING, Any
from uuid import uuid4

from deepmerge import always_merger
from django.db import models
from django.db.models import OuterRef, Subquery
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
from authentik.tasks.schedules.common import ScheduleSpec
from authentik.tasks.schedules.models import ScheduledModel

if TYPE_CHECKING:
    from authentik.endpoints.connector import BaseConnector


class Device(PolicyBindingModel):
    device_uuid = models.UUIDField(default=uuid4, primary_key=True)

    name = models.TextField()
    identifier = models.TextField(unique=True)
    connections = models.ManyToManyField("Connector", through="DeviceConnection")
    group = models.ForeignKey("DeviceGroup", null=True, on_delete=models.SET_DEFAULT, default=None)

    @cached_property
    def facts(self) -> DeviceFacts:
        data = {}
        for snapshot in DeviceFactSnapshot.filter_not_expired(
            snapshot_id__in=Subquery(
                DeviceFactSnapshot.objects.filter(
                    connection__connector=OuterRef("connection__connector"), connection__device=self
                )
                .order_by("-created")
                .values("snapshot_id")[:1]
            )
        ).values_list("data", flat=True):
            always_merger.merge(data, snapshot)
        return data


class DeviceUserBinding(PolicyBinding):
    is_primary = models.BooleanField(default=False)


class DeviceConnection(SerializerModel):
    device_connection_uuid = models.UUIDField(default=uuid4, primary_key=True)
    device = models.ForeignKey("Device", on_delete=models.CASCADE)
    connector = models.ForeignKey("Connector", on_delete=models.CASCADE)

    def create_snapshot(self, data: dict[str, Any]):
        expires = now() + timedelta_from_string(self.connector.snapshot_expiry)
        return DeviceFactSnapshot.objects.create(
            connection=self,
            data=data,
            expiring=True,
            expires=expires,
        )


class DeviceFactSnapshot(ExpiringModel, SerializerModel):
    snapshot_id = models.UUIDField(primary_key=True, default=uuid4)
    connection = models.ForeignKey(DeviceConnection, on_delete=models.CASCADE)
    data = models.JSONField(default=dict)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Device fact snapshot {self.snapshot_id} from {self.created}"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.endpoints.api.device_fact_snapshots import DeviceFactSnapshotSerializer

        return DeviceFactSnapshotSerializer


class Connector(ScheduledModel, SerializerModel):
    connector_uuid = models.UUIDField(default=uuid4, primary_key=True)

    name = models.TextField()
    enabled = models.BooleanField(default=True)
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

    @property
    def schedule_specs(self) -> list[ScheduleSpec]:
        from authentik.endpoints.tasks import endpoints_sync

        return [
            ScheduleSpec(
                actor=endpoints_sync,
                uid=self.name,
                args=(self.pk,),
                crontab="3-59/15 * * * *",
                send_on_save=True,
            ),
        ]


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
