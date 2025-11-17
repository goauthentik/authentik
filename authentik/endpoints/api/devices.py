from rest_framework.fields import SerializerMethodField
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.endpoints.api.device_connections import DeviceConnectionSerializer
from authentik.endpoints.api.device_group import DeviceGroupSerializer
from authentik.endpoints.facts import DeviceFacts
from authentik.endpoints.models import Device


class EndpointDeviceSerializer(ModelSerializer):

    connections_obj = DeviceConnectionSerializer(many=True, source="deviceconnection_set")
    group_obj = DeviceGroupSerializer(source="group")

    facts = SerializerMethodField()

    def get_facts(self, instance: Device) -> DeviceFacts:
        return instance.facts

    class Meta:
        model = Device
        fields = [
            "device_uuid",
            "pbm_uuid",
            "name",
            "group",
            "group_obj",
            "policies",
            "connections",
            "connections_obj",
            "facts",
            "expiring",
            "expires",
        ]


class DeviceViewSet(UsedByMixin, ModelViewSet):

    queryset = Device.objects.all().prefetch_related("policies", "connections")
    serializer_class = EndpointDeviceSerializer
    search_fields = [
        "name",
        "identifier",
    ]
    ordering = ["identifier"]
    filterset_fields = ["name", "identifier"]
