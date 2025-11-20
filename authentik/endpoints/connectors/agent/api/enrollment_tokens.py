from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.endpoints.api.device_group import DeviceGroupSerializer
from authentik.endpoints.connectors.agent.models import EnrollmentToken


class EnrollmentTokenSerializer(ModelSerializer):

    device_group_obj = DeviceGroupSerializer(source="device_group", read_only=True, required=False)

    class Meta:
        model = EnrollmentToken
        fields = [
            "token_uuid",
            "device_group",
            "device_group_obj",
            "connector",
            "name",
            "expiring",
            "expires",
        ]


class EnrollmentTokenViewSet(UsedByMixin, ModelViewSet):

    queryset = EnrollmentToken.objects.all().prefetch_related("device_group")
    serializer_class = EnrollmentTokenSerializer
    search_fields = [
        "name",
        "connector__name",
    ]
    ordering = ["token_uuid"]
    filterset_fields = ["token_uuid", "connector"]
