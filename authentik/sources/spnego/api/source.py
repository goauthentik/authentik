"""SPNEGOSource API Views"""
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.sources import SourceSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.sources.spnego.models import SPNEGOSource


class SPNEGOSourceSerializer(SourceSerializer):
    """SPNEGOSource Serializer"""

    class Meta:
        model = SPNEGOSource
        fields = SourceSerializer.Meta.fields + [
            "server_name",
            "keytab",
            "ccache",
            "guess_email",
        ]


class SPNEGOSourceViewSet(UsedByMixin, ModelViewSet):
    """SPNEGOSource Viewset"""

    queryset = SPNEGOSource.objects.all()
    serializer_class = SPNEGOSourceSerializer
    lookup_field = "slug"
    filterset_fields = [
        "name",
        "slug",
        "enabled",
        "authentication_flow",
        "enrollment_flow",
        "managed",
        "policy_engine_mode",
        "user_matching_mode",
        "server_name",
    ]
    search_fields = ["name", "slug", "server_name"]
    ordering = ["name"]
