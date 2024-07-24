"""Plex Source connection Serializer"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import ModelViewSet

from authentik.api.authorization import OwnerFilter, OwnerSuperuserPermissions
from authentik.core.api.sources import UserSourceConnectionSerializer, UserSourceConnectionViewSet
from authentik.core.api.used_by import UsedByMixin
from authentik.sources.plex.models import PlexSourceConnection


class PlexSourceConnectionSerializer(UserSourceConnectionSerializer):
    """Plex Source connection Serializer"""

    class Meta(UserSourceConnectionSerializer.Meta):
        model = PlexSourceConnection
        fields = UserSourceConnectionSerializer.Meta.fields + [
            "identifier",
            "plex_token",
        ]
        extra_kwargs = {
            **UserSourceConnectionSerializer.Meta.extra_kwargs,
            "plex_token": {"write_only": True},
        }


class PlexSourceConnectionViewSet(UserSourceConnectionViewSet, ModelViewSet):
    """Plex Source connection Serializer"""

    queryset = PlexSourceConnection.objects.all()
    serializer_class = PlexSourceConnectionSerializer
