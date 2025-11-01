from rest_framework.fields import SerializerMethodField
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.endpoints.api.device_connections import DeviceConnectionSerializer
from authentik.endpoints.common_data import CommonDeviceDataSerializer
from authentik.endpoints.models import Device


class EndpointDeviceSerializer(ModelSerializer):

    connections_obj = DeviceConnectionSerializer(many=True, source="deviceconnection_set")

    data = SerializerMethodField()

    def get_data(self, instance: Device) -> CommonDeviceDataSerializer:
        return instance.data

    class Meta:
        model = Device
        fields = [
            "device_uuid",
            "group",
            "policies",
            "connections",
            "connections_obj",
            "data",
        ]


class DeviceViewSet(UsedByMixin, ModelViewSet):

    queryset = Device.objects.all().prefetch_related("policies", "connections")
    serializer_class = EndpointDeviceSerializer
