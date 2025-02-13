"""RAC Provider API Views"""

from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from authentik.core.api.groups import GroupMemberSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.providers.rac.api.endpoints import EndpointSerializer
from authentik.providers.rac.api.providers import RACProviderSerializer
from authentik.providers.rac.models import ConnectionToken


class ConnectionTokenSerializer(EnterpriseRequiredMixin, ModelSerializer):
    """ConnectionToken Serializer"""

    provider_obj = RACProviderSerializer(source="provider", read_only=True)
    endpoint_obj = EndpointSerializer(source="endpoint", read_only=True)
    user = GroupMemberSerializer(source="session.user", read_only=True)

    class Meta:
        model = ConnectionToken
        fields = [
            "pk",
            "provider",
            "provider_obj",
            "endpoint",
            "endpoint_obj",
            "user",
        ]


class ConnectionTokenViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """ConnectionToken Viewset"""

    queryset = ConnectionToken.objects.all().select_related("session", "endpoint")
    serializer_class = ConnectionTokenSerializer
    filterset_fields = ["endpoint", "session__user", "provider"]
    search_fields = ["endpoint__name", "provider__name"]
    ordering = ["endpoint__name", "provider__name"]
    owner_field = "session__user"
