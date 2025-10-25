"""SCIMSourceGroup API Views"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.sources import SourceSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.users import PartialGroupSerializer
from authentik.sources.scim.models import SCIMSourceGroup


class SCIMSourceGroupSerializer(SourceSerializer):
    """SCIMSourceGroup Serializer"""

    group_obj = PartialGroupSerializer(source="group", read_only=True)

    class Meta:

        model = SCIMSourceGroup
        fields = [
            "id",
            "external_id",
            "group",
            "group_obj",
            "source",
            "attributes",
        ]


class SCIMSourceGroupViewSet(UsedByMixin, ModelViewSet):
    """SCIMSourceGroup Viewset"""

    queryset = SCIMSourceGroup.objects.all().select_related("group")
    serializer_class = SCIMSourceGroupSerializer
    filterset_fields = ["source__slug", "group__name", "group__group_uuid"]
    search_fields = ["source__slug", "group__name", "attributes", "external_id"]
    ordering = ["group__name"]
