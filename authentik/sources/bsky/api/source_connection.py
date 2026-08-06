from rest_framework.viewsets import ModelViewSet

from authentik.core.api.sources import (
    GroupSourceConnectionSerializer,
    GroupSourceConnectionViewSet,
    UserSourceConnectionSerializer,
    UserSourceConnectionViewSet,
)
from authentik.sources.bsky.models import GroupBskySourceConnection, UserBskySourceConnection


class UserBskySourceConnectionSerializer(UserSourceConnectionSerializer):
    class Meta(UserSourceConnectionSerializer.Meta):
        model = UserBskySourceConnection
        fields = UserSourceConnectionSerializer.Meta.fields + [
            "access_token",
            "refresh_token",
            "expires",
        ]
        extra_kwargs = {
            **UserSourceConnectionSerializer.Meta.extra_kwargs,
            "access_token": {"write_only": True},
            "refresh_token": {"write_only": True},
        }


class UserBskySourceConnectionViewSet(
    UserSourceConnectionViewSet, ModelViewSet[UserBskySourceConnection]
):
    queryset = UserBskySourceConnection.objects.all()
    serializer_class = UserBskySourceConnectionSerializer


class GroupBskySourceConnectionSerializer(GroupSourceConnectionSerializer):
    class Meta(GroupSourceConnectionSerializer.Meta):
        model = GroupBskySourceConnection


class GroupBskySourceConnectionViewSet(
    GroupSourceConnectionViewSet, ModelViewSet[GroupBskySourceConnection]
):
    queryset = GroupBskySourceConnection.objects.all()
    serializer_class = GroupBskySourceConnectionSerializer
