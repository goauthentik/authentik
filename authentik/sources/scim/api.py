"""SCIMSource API Views"""
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.sources import SourceSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.sources.scim.models import SCIMSource


class SCIMSourceSerializer(SourceSerializer):
    """SCIMSource Serializer"""

    class Meta:

        model = SCIMSource
        fields = SourceSerializer.Meta.fields + ["token"]


class SCIMSourceViewSet(UsedByMixin, ModelViewSet):
    """SCIMSource Viewset"""

    queryset = SCIMSource.objects.all()
    serializer_class = SCIMSourceSerializer
    lookup_field = "slug"
    filterset_fields = "__all__"
    search_fields = ["name", "slug"]
    ordering = ["name"]
