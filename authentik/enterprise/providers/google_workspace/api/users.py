"""GoogleWorkspaceProviderUser API Views"""

from authentik.core.api.groups import PartialUserSerializer
from authentik.core.api.utils import ModelSerializer
from authentik.enterprise.providers.google_workspace.models import GoogleWorkspaceProviderUser
from authentik.lib.sync.outgoing.api import OutgoingSyncConnectionViewSet


class GoogleWorkspaceProviderUserSerializer(ModelSerializer):
    """GoogleWorkspaceProviderUser Serializer"""

    user_obj = PartialUserSerializer(source="user", read_only=True)

    class Meta:
        model = GoogleWorkspaceProviderUser
        fields = [
            "id",
            "google_id",
            "user",
            "user_obj",
            "provider",
            "attributes",
        ]
        extra_kwargs = {"attributes": {"read_only": True}}


class GoogleWorkspaceProviderUserViewSet(OutgoingSyncConnectionViewSet):
    """GoogleWorkspaceProviderUser Viewset"""

    queryset = GoogleWorkspaceProviderUser.objects.all().select_related("user")
    serializer_class = GoogleWorkspaceProviderUserSerializer
    filterset_fields = ["provider__id", "user__username", "user__id"]
    search_fields = ["provider__name", "user__username"]
    ordering = ["user__username"]
