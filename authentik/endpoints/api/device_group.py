from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.endpoints.models import DeviceGroup


class DeviceGroupSerializer(ModelSerializer):

    class Meta:
        model = DeviceGroup
        fields = [
            "pbm_uuid",
            "name",
        ]


class DeviceGroupViewSet(UsedByMixin, ModelViewSet):
    """DeviceGroup Viewset"""

    queryset = DeviceGroup.objects.all()
    serializer_class = DeviceGroupSerializer
    search_fields = [
        "pbm_uuid",
        "name",
    ]
    filterset_fields = [
        "pbm_uuid",
        "name",
    ]
    ordering = ["name"]
