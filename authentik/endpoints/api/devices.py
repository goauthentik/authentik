"""Device API Views"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.endpoints.models import Device


class DeviceSerializer(ModelSerializer):
    """Device Serializer"""

    class Meta:
        model = Device
        fields = [
            "pk",
            "identifier",
            "users",
            "connections",
        ]


class DeviceViewSet(UsedByMixin, ModelViewSet):
    """Device Viewset"""

    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    filterset_fields = [
        "identifier",
    ]
    search_fields = ["identifier"]
    ordering = ["identifier"]
