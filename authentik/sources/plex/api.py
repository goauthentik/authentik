"""Plex Source Serializer"""
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.sources import SourceSerializer
from authentik.sources.plex.models import PlexSource


class PlexSourceSerializer(SourceSerializer):
    """Plex Source Serializer"""

    class Meta:
        model = PlexSource
        fields = SourceSerializer.Meta.fields + ["client_id", "allowed_servers"]


class PlexSourceViewSet(ModelViewSet):
    """Plex source Viewset"""

    queryset = PlexSource.objects.all()
    serializer_class = PlexSourceSerializer
    lookup_field = "slug"
