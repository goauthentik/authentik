"""Plex Source connection Serializer"""
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import ModelViewSet

from authentik.api.authorization import OwnerFilter, OwnerSuperuserPermissions
from authentik.core.api.sources import UserSourceConnectionSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.sources.plex.models import PlexSourceConnection


class PlexSourceConnectionSerializer(UserSourceConnectionSerializer):
    """Plex Source connection Serializer"""

    class Meta:
        model = PlexSourceConnection
        fields = [
            "pk",
            "user",
            "source",
            "identifier",
            "plex_token",
        ]
        extra_kwargs = {
            "user": {"read_only": True},
        }


class PlexSourceConnectionViewSet(UsedByMixin, ModelViewSet):
    """Plex Source connection Serializer"""

    queryset = PlexSourceConnection.objects.all()
    serializer_class = PlexSourceConnectionSerializer
    filterset_fields = ["source__slug"]
    permission_classes = [OwnerSuperuserPermissions]
    filter_backends = [OwnerFilter, DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering = ["pk"]
    search_fields = ["source__slug"]
