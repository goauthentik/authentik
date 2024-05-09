"""GoogleWorkspaceProviderUser API Views"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.groups import GroupMemberSerializer
from authentik.core.api.sources import SourceSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.enterprise.providers.google_workspace.models import GoogleWorkspaceProviderUser


class GoogleWorkspaceProviderUserSerializer(SourceSerializer):
    """GoogleWorkspaceProviderUser Serializer"""

    user_obj = GroupMemberSerializer(source="user", read_only=True)

    class Meta:

        model = GoogleWorkspaceProviderUser
        fields = [
            "id",
            "user",
            "user_obj",
        ]


class GoogleWorkspaceProviderUserViewSet(UsedByMixin, ModelViewSet):
    """GoogleWorkspaceProviderUser Viewset"""

    queryset = GoogleWorkspaceProviderUser.objects.all().select_related("user")
    serializer_class = GoogleWorkspaceProviderUserSerializer
    filterset_fields = ["provider__id", "user__username", "user__id"]
    search_fields = ["provider__name", "user__username"]
    ordering = ["user__username"]
