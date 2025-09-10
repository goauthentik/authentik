from rest_framework.fields import SerializerMethodField
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.endpoints.api.device_connections import DeviceConnectionSerializer
from authentik.endpoints.api.device_users import DeviceUserSerializer
from authentik.endpoints.common_data import CommonDeviceDataSerializer
from authentik.endpoints.models import Device


class EndpointDeviceSerializer(ModelSerializer):

    users_obj = DeviceUserSerializer(many=True, source="deviceuser_set")
    connections_obj = DeviceConnectionSerializer(many=True, source="deviceconnection_set")

    data = SerializerMethodField()

    def get_data(self, instance: Device) -> CommonDeviceDataSerializer:
        return instance.data

    class Meta:
        model = Device
        fields = [
            "device_uuid",
            "group",
            "users",
            "users_obj",
            "connections",
            "connections_obj",
            "data",
        ]


class DeviceViewSet(UsedByMixin, ModelViewSet):

    queryset = Device.objects.all()
    serializer_class = EndpointDeviceSerializer
