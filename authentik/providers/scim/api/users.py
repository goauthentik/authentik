"""SCIMProviderUser API Views"""

from authentik.core.api.groups import PartialUserSerializer
from authentik.core.api.utils import ModelSerializer
from authentik.lib.sync.outgoing.api import OutgoingSyncConnectionViewSet
from authentik.providers.scim.models import SCIMProviderUser


class SCIMProviderUserSerializer(ModelSerializer):
    """SCIMProviderUser Serializer"""

    user_obj = PartialUserSerializer(source="user", read_only=True)

    class Meta:
        model = SCIMProviderUser
        fields = [
            "id",
            "scim_id",
            "user",
            "user_obj",
            "provider",
            "attributes",
        ]
        extra_kwargs = {"attributes": {"read_only": True}}


class SCIMProviderUserViewSet(OutgoingSyncConnectionViewSet):
    """SCIMProviderUser Viewset"""

    queryset = SCIMProviderUser.objects.all().select_related("user")
    serializer_class = SCIMProviderUserSerializer
    filterset_fields = ["provider__id", "user__username", "user__id"]
    search_fields = ["provider__name", "user__username"]
    ordering = ["user__username"]
