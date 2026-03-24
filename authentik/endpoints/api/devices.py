from datetime import timedelta

from django.db.models import OuterRef, Subquery
from django.utils.timezone import now
from drf_spectacular.utils import extend_schema
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.fields import IntegerField, SerializerMethodField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer, PassiveSerializer
from authentik.endpoints.api.device_access_group import DeviceAccessGroupSerializer
from authentik.endpoints.api.device_connections import DeviceConnectionSerializer
from authentik.endpoints.api.device_fact_snapshots import DeviceFactSnapshotSerializer
from authentik.endpoints.models import Device, DeviceFactSnapshot


class EndpointDeviceSerializer(ModelSerializer):

    access_group_obj = DeviceAccessGroupSerializer(source="access_group", required=False)

    facts = SerializerMethodField()

    def get_facts(self, instance: Device) -> DeviceFactSnapshotSerializer:
        return DeviceFactSnapshotSerializer(instance.cached_facts).data

    class Meta:
        model = Device
        fields = [
            "device_uuid",
            "pbm_uuid",
            "name",
            "access_group",
            "access_group_obj",
            "expiring",
            "expires",
            "facts",
            "attributes",
        ]


class EndpointDeviceDetailsSerializer(EndpointDeviceSerializer):

    connections_obj = DeviceConnectionSerializer(many=True, source="deviceconnection_set")

    def get_facts(self, instance: Device) -> DeviceFactSnapshotSerializer:
        return DeviceFactSnapshotSerializer(instance.facts).data

    class Meta(EndpointDeviceSerializer.Meta):
        fields = EndpointDeviceSerializer.Meta.fields + [
            "connections_obj",
            "policies",
            "connections",
        ]


class DeviceViewSet(
    UsedByMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):

    queryset = Device.objects.all().select_related("access_group")
    serializer_class = EndpointDeviceSerializer
    search_fields = [
        "name",
        "identifier",
    ]
    ordering = ["identifier"]
    filterset_fields = ["name", "identifier"]

    class DeviceSummarySerializer(PassiveSerializer):
        """Summary of registered devices"""

        total_count = IntegerField()
        unreachable_count = IntegerField()
        outdated_agent_count = IntegerField()

    def get_serializer_class(self):
        if self.action == "retrieve":
            return EndpointDeviceDetailsSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        if self.action == "retrieve":
            return super().get_queryset().prefetch_related("connections")
        return super().get_queryset()

    @extend_schema(responses={200: DeviceSummarySerializer()})
    @action(methods=["GET"], detail=False)
    def summary(self, request: Request) -> Response:
        delta = now() - timedelta(hours=24)
        unreachable = (
            Device.objects.all()
            .annotate(
                latest_snapshot=Subquery(
                    DeviceFactSnapshot.objects.filter(connection__device=OuterRef("pk"))
                    .order_by("-created")
                    .values("created")[:1]
                )
            )
            .filter(latest_snapshot__lte=delta)
            .distinct()
            .count()
        )
        data = {
            "total_count": Device.objects.all().count(),
            "unreachable_count": unreachable,
            # Currently not supported
            "outdated_agent_count": 0,
        }
        return Response(data)
