"""GoogleWorkspaceProviderUser API Views"""

from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from authentik.common.sync.outgoing.api import OutgoingSyncConnectionCreateMixin
from authentik.core.api.groups import GroupMemberSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.enterprise.providers.google_workspace.models import GoogleWorkspaceProviderUser


class GoogleWorkspaceProviderUserSerializer(ModelSerializer):
    """GoogleWorkspaceProviderUser Serializer"""

    user_obj = GroupMemberSerializer(source="user", read_only=True)

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


class GoogleWorkspaceProviderUserViewSet(
    mixins.CreateModelMixin,
    OutgoingSyncConnectionCreateMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """GoogleWorkspaceProviderUser Viewset"""

    queryset = GoogleWorkspaceProviderUser.objects.all().select_related("user")
    serializer_class = GoogleWorkspaceProviderUserSerializer
    filterset_fields = ["provider__id", "user__username", "user__id"]
    search_fields = ["provider__name", "user__username"]
    ordering = ["user__username"]
