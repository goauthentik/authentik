"""MicrosoftEntraProviderUser API Views"""

from authentik.core.api.groups import PartialUserSerializer
from authentik.core.api.utils import ModelSerializer
from authentik.enterprise.providers.microsoft_entra.models import MicrosoftEntraProviderUser
from authentik.lib.sync.outgoing.api import OutgoingSyncConnectionViewSet


class MicrosoftEntraProviderUserSerializer(ModelSerializer):
    """MicrosoftEntraProviderUser Serializer"""

    user_obj = PartialUserSerializer(source="user", read_only=True)

    class Meta:
        model = MicrosoftEntraProviderUser
        fields = [
            "id",
            "microsoft_id",
            "user",
            "user_obj",
            "provider",
            "attributes",
        ]
        extra_kwargs = {"attributes": {"read_only": True}}


class MicrosoftEntraProviderUserViewSet(OutgoingSyncConnectionViewSet):
    """MicrosoftEntraProviderUser Viewset"""

    queryset = MicrosoftEntraProviderUser.objects.all().select_related("user")
    serializer_class = MicrosoftEntraProviderUserSerializer
    filterset_fields = ["provider__id", "user__username", "user__id"]
    search_fields = ["provider__name", "user__username"]
    ordering = ["user__username"]
