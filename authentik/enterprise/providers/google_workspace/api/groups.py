"""GoogleWorkspaceProviderGroup API Views"""

from authentik.core.api.users import PartialGroupSerializer
from authentik.core.api.utils import ModelSerializer
from authentik.enterprise.providers.google_workspace.models import GoogleWorkspaceProviderGroup
from authentik.lib.sync.outgoing.api import OutgoingSyncConnectionViewSet


class GoogleWorkspaceProviderGroupSerializer(ModelSerializer):
    """GoogleWorkspaceProviderGroup Serializer"""

    group_obj = PartialGroupSerializer(source="group", read_only=True)

    class Meta:
        model = GoogleWorkspaceProviderGroup
        fields = [
            "id",
            "google_id",
            "group",
            "group_obj",
            "provider",
            "attributes",
        ]
        extra_kwargs = {"attributes": {"read_only": True}}


class GoogleWorkspaceProviderGroupViewSet(OutgoingSyncConnectionViewSet):
    """GoogleWorkspaceProviderGroup Viewset"""

    queryset = GoogleWorkspaceProviderGroup.objects.all().select_related("group")
    serializer_class = GoogleWorkspaceProviderGroupSerializer
    filterset_fields = ["provider__id", "group__name", "group__group_uuid"]
    search_fields = ["provider__name", "group__name"]
    ordering = ["group__name"]
