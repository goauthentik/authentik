from datetime import timedelta
from uuid import uuid4

from django.db.models import OuterRef, Prefetch, Subquery
from django.utils.timezone import now
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.fields import IntegerField, SerializerMethodField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer, PassiveSerializer
from authentik.endpoints.api.device_access_group import DeviceAccessGroupSerializer
from authentik.endpoints.api.device_connections import DeviceConnectionSerializer
from authentik.endpoints.api.device_fact_snapshots import DeviceFactSnapshotSerializer
from authentik.endpoints.api.device_user_bindings import DeviceUserBindingSerializer
from authentik.endpoints.models import Device, DeviceFactSnapshot, DeviceUserBinding
from authentik.providers.rac.api.connection_overrides import RACConnectionOverrideSerializer
from authentik.providers.rac.models import RACConnectionOverride


class EndpointDeviceSerializer(ModelSerializer):

    access_group_obj = DeviceAccessGroupSerializer(source="access_group", required=False)

    facts = SerializerMethodField(allow_null=True)

    primary_binding_obj = DeviceUserBindingSerializer(
        source="primary_user_binding", read_only=True, allow_null=True
    )

    rac = RACConnectionOverrideSerializer(source="rac_override", allow_null=True)

    def get_facts(self, instance: Device) -> DeviceFactSnapshotSerializer:
        try:
            return DeviceFactSnapshotSerializer(instance.cached_facts).data
        except KeyError, AttributeError:
            return None

    def validate(self, attrs: dict) -> dict:
        attrs = super().validate(attrs)
        # A device which is added through the API is not enrolled by a connector, so it
        # cannot report how it is reached and has to be told
        if not self.instance and not attrs.get("rac_override"):
            raise ValidationError({"rac": "This field is required."})
        return attrs

    def create(self, validated_data: dict) -> Device:
        """Devices created through the API are not enrolled by a connector, so they get
        a generated identifier and don't expire."""
        override = validated_data.pop("rac_override")
        validated_data.setdefault("identifier", f"manual://{uuid4()}")
        validated_data.setdefault("expiring", False)
        device = super().create(validated_data)
        RACConnectionOverride.objects.create(device=device, **override)
        return device

    def update(self, instance: Device, validated_data: dict) -> Device:
        override = validated_data.pop("rac_override", None)
        device = super().update(instance, validated_data)
        if override:
            RACConnectionOverride.objects.update_or_create(device=device, defaults=override)
        return device

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
            "primary_binding_obj",
            "rac",
        ]


class EndpointDeviceDetailsSerializer(EndpointDeviceSerializer):

    connections_obj = DeviceConnectionSerializer(many=True, source="deviceconnection_set")

    def get_facts(self, instance: Device) -> DeviceFactSnapshotSerializer:
        try:
            return DeviceFactSnapshotSerializer(instance.facts).data
        except KeyError, AttributeError:
            return None

    class Meta(EndpointDeviceSerializer.Meta):
        fields = EndpointDeviceSerializer.Meta.fields + [
            "connections_obj",
            "policies",
            "connections",
        ]


class DeviceViewSet(UsedByMixin, ModelViewSet):

    queryset = (
        Device.objects.all()
        .select_related("access_group")
        .prefetch_related(
            Prefetch("bindings", queryset=DeviceUserBinding.objects.all(), to_attr="user_bindings")
        )
    )
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
