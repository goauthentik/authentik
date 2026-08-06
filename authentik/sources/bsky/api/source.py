from rest_framework.viewsets import ModelViewSet

from authentik.core.api.sources import SourceSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.sources.bsky.models import BskySource


class BskySourceSerializer(SourceSerializer):
    """Bsky Source Serializer"""

    class Meta:
        model = BskySource
        fields = SourceSerializer.Meta.fields + [
            "group_matching_mode",
            "scope",
        ]


class BskySourceViewSet(UsedByMixin, ModelViewSet[BskySource]):
    """Bsky source Viewset"""

    queryset = BskySource.objects.all()
    serializer_class = BskySourceSerializer
    lookup_field = "slug"
    filterset_fields = [
        "pbm_uuid",
        "name",
        "slug",
        "enabled",
        "authentication_flow",
        "enrollment_flow",
    ]
    search_fields = ["name", "slug"]
    ordering = ["name"]
