"""RAC Provider API Views"""

from rest_framework import mixins
from rest_framework.fields import CharField
from rest_framework.viewsets import GenericViewSet

from authentik.core.api.groups import PartialUserSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.providers.rac.api.providers import RACProviderSerializer
from authentik.providers.rac.models import ConnectionToken


class ConnectionTokenSerializer(ModelSerializer):
    """ConnectionToken Serializer"""

    provider_obj = RACProviderSerializer(source="provider", read_only=True)
    # Only the name is exposed, as a device's attributes can hold connection
    # credentials and this endpoint is readable by the user owning the token
    device_name = CharField(source="device.name", read_only=True)
    user = PartialUserSerializer(source="session.user", read_only=True)

    class Meta:
        model = ConnectionToken
        fields = [
            "pk",
            "provider",
            "provider_obj",
            "device",
            "device_name",
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

    queryset = ConnectionToken.objects.including_expired().all().select_related("session", "device")
    serializer_class = ConnectionTokenSerializer
    filterset_fields = ["device", "session__user", "provider"]
    search_fields = ["device__name", "provider__name"]
    ordering = ["device__name", "provider__name"]
    owner_field = "session__user"
