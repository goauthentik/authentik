from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.endpoints.models import DeviceAccessGroup


class DeviceAccessGroupSerializer(ModelSerializer):

    class Meta:
        model = DeviceAccessGroup
        fields = [
            "pbm_uuid",
            "name",
        ]


class DeviceAccessGroupViewSet(UsedByMixin, ModelViewSet):
    """DeviceAccessGroup Viewset"""

    queryset = DeviceAccessGroup.objects.all()
    serializer_class = DeviceAccessGroupSerializer
    search_fields = [
        "pbm_uuid",
        "name",
    ]
    filterset_fields = [
        "pbm_uuid",
        "name",
    ]
    ordering = ["name"]
