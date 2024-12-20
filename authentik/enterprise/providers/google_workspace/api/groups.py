"""GoogleWorkspaceProviderGroup API Views"""

from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.users import UserGroupSerializer
from authentik.core.api.utils import ModelSerializer
from authentik.enterprise.providers.google_workspace.models import GoogleWorkspaceProviderGroup
from authentik.lib.sync.outgoing.api import OutgoingSyncConnectionCreateMixin


class GoogleWorkspaceProviderGroupSerializer(ModelSerializer):
    """GoogleWorkspaceProviderGroup Serializer"""

    group_obj = UserGroupSerializer(source="group", read_only=True)

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


class GoogleWorkspaceProviderGroupViewSet(
    mixins.CreateModelMixin,
    OutgoingSyncConnectionCreateMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """GoogleWorkspaceProviderGroup Viewset"""

    queryset = GoogleWorkspaceProviderGroup.objects.all().select_related("group")
    serializer_class = GoogleWorkspaceProviderGroupSerializer
    filterset_fields = ["provider__id", "group__name", "group__group_uuid"]
    search_fields = ["provider__name", "group__name"]
    ordering = ["group__name"]
