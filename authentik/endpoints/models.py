from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from django.core.cache import cache
from django.db import models
from django.db.models import OuterRef, Subquery
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from model_utils.managers import InheritanceManager
from rest_framework.serializers import Serializer
from structlog.stdlib import get_logger

from authentik.core.models import AttributesMixin, ExpiringModel
from authentik.flows.models import Stage
from authentik.flows.stage import StageView
from authentik.lib.merge import MERGE_LIST_UNIQUE
from authentik.lib.models import InheritanceForeignKey, SerializerModel
from authentik.lib.utils.time import timedelta_from_string, timedelta_string_validator
from authentik.policies.models import PolicyBinding, PolicyBindingModel
from authentik.tasks.schedules.common import ScheduleSpec
from authentik.tasks.schedules.models import ScheduledModel

if TYPE_CHECKING:
    from authentik.endpoints.controller import BaseController

LOGGER = get_logger()
DEVICE_FACTS_CACHE_TIMEOUT = 3600


class Device(ExpiringModel, AttributesMixin, PolicyBindingModel):
    device_uuid = models.UUIDField(default=uuid4, primary_key=True)

    name = models.TextField(unique=True)
    identifier = models.TextField(unique=True)
    connections = models.ManyToManyField("Connector", through="DeviceConnection")
    tags = models.ManyToManyField("DeviceTag", blank=True)

    @property
    def cache_key_facts(self):
        return f"goauthentik.io/endpoints/devices/{self.device_uuid}/facts"

    @property
    def cached_facts(self) -> "DeviceFactSnapshot":
        if cached := cache.get(self.cache_key_facts):
            return cached
        facts = self.facts
        cache.set(self.cache_key_facts, facts, timeout=DEVICE_FACTS_CACHE_TIMEOUT)
        return facts

    @property
    def facts(self) -> "DeviceFactSnapshot":
        data = {}
        last_updated = datetime.fromtimestamp(0, UTC)
        for snapshot_data, snapshort_created in DeviceFactSnapshot.filter_not_expired(
            snapshot_id__in=Subquery(
                DeviceFactSnapshot.objects.filter(
                    connection__connector=OuterRef("connection__connector"), connection__device=self
                )
                .order_by("-created")
                .values("snapshot_id")[:1]
            )
        ).values_list("data", "created"):
            MERGE_LIST_UNIQUE.merge(data, snapshot_data)
            last_updated = max(last_updated, snapshort_created)
        return DeviceFactSnapshot(data=data, created=last_updated)

    def __str__(self):
        return f"Device {self.name} {self.identifier} ({self.pk})"

    class Meta(ExpiringModel.Meta):
        verbose_name = _("Device")
        verbose_name_plural = _("Devices")


class DeviceUserBinding(PolicyBinding):
    is_primary = models.BooleanField(default=False)
    # Used for storing a reference to the connector if this user/group binding was created
    # by a connector and not manually
    connector = models.ForeignKey("Connector", on_delete=models.CASCADE, null=True)

    class Meta(PolicyBinding.Meta):
        verbose_name = _("Device User binding")
        verbose_name_plural = _("Device User bindings")


class DeviceConnection(SerializerModel):
    device_connection_uuid = models.UUIDField(default=uuid4, primary_key=True)
    device = models.ForeignKey("Device", on_delete=models.CASCADE)
    connector = models.ForeignKey("Connector", on_delete=models.CASCADE)

    def create_snapshot(self, data: dict[str, Any]):
        expires = now() + timedelta_from_string(self.connector.snapshot_expiry)
        # If this is the first snapshot for this connection, purge the cache
        if not DeviceFactSnapshot.objects.filter(connection=self).exists():
            LOGGER.debug("Purging facts cache for device", device=self.device)
            cache.delete(self.device.cache_key_facts)
        return DeviceFactSnapshot.objects.create(
            connection=self,
            data=data,
            expiring=True,
            expires=expires,
        )

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.endpoints.api.device_connections import DeviceConnectionSerializer

        return DeviceConnectionSerializer

    class Meta:
        verbose_name = _("Device connection")
        verbose_name_plural = _("Device connections")


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

    class Meta(ExpiringModel.Meta):
        verbose_name = _("Device fact snapshot")
        verbose_name_plural = _("Device fact snapshots")


class Connector(ScheduledModel, SerializerModel):
    connector_uuid = models.UUIDField(default=uuid4, primary_key=True)

    name = models.TextField()
    enabled = models.BooleanField(default=True)

    snapshot_expiry = models.TextField(
        default="hours=24",
        validators=[timedelta_string_validator],
    )

    objects = InheritanceManager()

    @property
    def component(self) -> str:
        raise NotImplementedError

    @property
    def controller(self) -> type["BaseController[Connector]"]:
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


class DeviceTag(PolicyBindingModel):

    name = models.TextField(unique=True)
    generated_by = models.ForeignKey(Connector, on_delete=models.CASCADE, null=True, default=None)

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.endpoints.api.device_tags import DeviceTagSerializer

        return DeviceTagSerializer

    class Meta:
        verbose_name = _("Device tag")
        verbose_name_plural = _("Device tags")


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
