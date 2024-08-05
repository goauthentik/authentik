"""Plex Source connection Serializer"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.sources import (
    GroupSourceConnectionSerializer,
    GroupSourceConnectionViewSet,
    UserSourceConnectionSerializer,
    UserSourceConnectionViewSet,
)
from authentik.sources.plex.models import GroupPlexSourceConnection, UserPlexSourceConnection


class UserPlexSourceConnectionSerializer(UserSourceConnectionSerializer):
    """Plex Source connection Serializer"""

    class Meta(UserSourceConnectionSerializer.Meta):
        model = UserPlexSourceConnection
        fields = UserSourceConnectionSerializer.Meta.fields + [
            "identifier",
            "plex_token",
        ]
        extra_kwargs = {
            **UserSourceConnectionSerializer.Meta.extra_kwargs,
            "plex_token": {"write_only": True},
        }


class UserPlexSourceConnectionViewSet(UserSourceConnectionViewSet, ModelViewSet):
    """Plex Source connection Serializer"""

    queryset = UserPlexSourceConnection.objects.all()
    serializer_class = UserPlexSourceConnectionSerializer


class GroupPlexSourceConnectionSerializer(GroupSourceConnectionSerializer):
    """Plex Group-Source connection Serializer"""

    class Meta(GroupSourceConnectionSerializer.Meta):
        model = GroupPlexSourceConnection


class GroupPlexSourceConnectionViewSet(GroupSourceConnectionViewSet, ModelViewSet):
    """Group-source connection Viewset"""

    queryset = GroupPlexSourceConnection.objects.all()
    serializer_class = GroupPlexSourceConnectionSerializer
