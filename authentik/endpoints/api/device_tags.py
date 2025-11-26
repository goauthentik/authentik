from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.endpoints.models import DeviceTag


class DeviceTagSerializer(ModelSerializer):

    class Meta:
        model = DeviceTag
        fields = [
            "pbm_uuid",
            "name",
        ]


class DeviceTagViewSet(UsedByMixin, ModelViewSet):
    """DeviceTag Viewset"""

    queryset = DeviceTag.objects.all()
    serializer_class = DeviceTagSerializer
    search_fields = [
        "pbm_uuid",
        "name",
    ]
    filterset_fields = [
        "pbm_uuid",
        "name",
    ]
    ordering = ["name"]
