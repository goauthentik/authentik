from rest_framework import mixins
from rest_framework.fields import SerializerMethodField
from rest_framework.viewsets import GenericViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.endpoints.api.device_access_group import DeviceAccessGroupSerializer
from authentik.endpoints.api.device_connections import DeviceConnectionSerializer
from authentik.endpoints.api.device_fact_snapshots import DeviceFactSnapshotSerializer
from authentik.endpoints.models import Device


class EndpointDeviceSerializer(ModelSerializer):

    access_group_obj = DeviceAccessGroupSerializer(source="access_group")

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

    def get_serializer_class(self):
        if self.action == "retrieve":
            return EndpointDeviceDetailsSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        if self.action == "retrieve":
            return super().get_queryset().prefetch_related("connections")
        return super().get_queryset()
