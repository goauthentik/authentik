"""GoogleWorkspaceProviderGroup API Views"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.sources import SourceSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.users import UserGroupSerializer
from authentik.enterprise.providers.google_workspace.models import GoogleWorkspaceProviderGroup


class GoogleWorkspaceProviderGroupSerializer(SourceSerializer):
    """GoogleWorkspaceProviderGroup Serializer"""

    group_obj = UserGroupSerializer(source="group", read_only=True)

    class Meta:

        model = GoogleWorkspaceProviderGroup
        fields = [
            "id",
            "group",
            "group_obj",
        ]


class GoogleWorkspaceProviderGroupViewSet(UsedByMixin, ModelViewSet):
    """GoogleWorkspaceProviderGroup Viewset"""

    queryset = GoogleWorkspaceProviderGroup.objects.all().select_related("group")
    serializer_class = GoogleWorkspaceProviderGroupSerializer
    filterset_fields = ["provider__id", "group__name", "group__group_uuid"]
    search_fields = ["provider__name", "group__name"]
    ordering = ["group__name"]
