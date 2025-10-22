"""SCIMProviderGroup API Views"""

from authentik.core.api.users import PartialGroupSerializer
from authentik.core.api.utils import ModelSerializer
from authentik.lib.sync.outgoing.api import OutgoingSyncConnectionViewSet
from authentik.providers.scim.models import SCIMProviderGroup


class SCIMProviderGroupSerializer(ModelSerializer):
    """SCIMProviderGroup Serializer"""

    group_obj = PartialGroupSerializer(source="group", read_only=True)

    class Meta:
        model = SCIMProviderGroup
        fields = [
            "id",
            "scim_id",
            "group",
            "group_obj",
            "provider",
            "attributes",
        ]
        extra_kwargs = {"attributes": {"read_only": True}}


class SCIMProviderGroupViewSet(OutgoingSyncConnectionViewSet):
    """SCIMProviderGroup Viewset"""

    queryset = SCIMProviderGroup.objects.all().select_related("group")
    serializer_class = SCIMProviderGroupSerializer
    filterset_fields = ["provider__id", "group__name", "group__group_uuid"]
    search_fields = ["provider__name", "group__name"]
    ordering = ["group__name"]
