"""MicrosoftEntraProviderGroup API Views"""

from authentik.core.api.users import PartialGroupSerializer
from authentik.core.api.utils import ModelSerializer
from authentik.enterprise.providers.microsoft_entra.models import MicrosoftEntraProviderGroup
from authentik.lib.sync.outgoing.api import OutgoingSyncConnectionViewSet


class MicrosoftEntraProviderGroupSerializer(ModelSerializer):
    """MicrosoftEntraProviderGroup Serializer"""

    group_obj = PartialGroupSerializer(source="group", read_only=True)

    class Meta:
        model = MicrosoftEntraProviderGroup
        fields = [
            "id",
            "microsoft_id",
            "group",
            "group_obj",
            "provider",
            "attributes",
        ]
        extra_kwargs = {"attributes": {"read_only": True}}


class MicrosoftEntraProviderGroupViewSet(OutgoingSyncConnectionViewSet):
    """MicrosoftEntraProviderGroup Viewset"""

    queryset = MicrosoftEntraProviderGroup.objects.all().select_related("group")
    serializer_class = MicrosoftEntraProviderGroupSerializer
    filterset_fields = ["provider__id", "group__name", "group__group_uuid"]
    search_fields = ["provider__name", "group__name"]
    ordering = ["group__name"]
