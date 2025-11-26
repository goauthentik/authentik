from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.endpoints.api.device_tags import DeviceTagSerializer
from authentik.endpoints.connectors.agent.models import AuthenticationProfile


class AuthenticationProfileSerializer(ModelSerializer):

    tags_obj = DeviceTagSerializer(source="tags", many=True, read_only=True, required=False)

    class Meta:
        model = AuthenticationProfile
        fields = [
            "pbm_uuid",
            "name",
            "tags",
            "tags_obj",
            "authorization_flow",
            "auth_terminate_session_on_expiry",
            "jwt_federation_providers",
        ]


class AuthenticationProfileViewSet(UsedByMixin, ModelViewSet):

    queryset = AuthenticationProfile.objects.all().prefetch_related("tags")
    serializer_class = AuthenticationProfileSerializer
    search_fields = [
        "name",
    ]
    ordering = ["name"]
    filterset_fields = ["name"]
