from rest_framework.viewsets import ModelViewSet

from authentik.core.api.sources import (
    GroupSourceConnectionSerializer,
    GroupSourceConnectionViewSet,
    UserSourceConnectionSerializer,
    UserSourceConnectionViewSet,
)
from authentik.sources.oauth.models import GroupOAuthSourceConnection, UserOAuthSourceConnection


class UserOAuthSourceConnectionSerializer(UserSourceConnectionSerializer):
    class Meta(UserSourceConnectionSerializer.Meta):
        model = UserOAuthSourceConnection
        fields = UserSourceConnectionSerializer.Meta.fields + ["identifier", "access_token"]
        extra_kwargs = {
            **UserSourceConnectionSerializer.Meta.extra_kwargs,
            "access_token": {"write_only": True},
        }


class UserOAuthSourceConnectionViewSet(UserSourceConnectionViewSet, ModelViewSet):
    queryset = UserOAuthSourceConnection.objects.all()
    serializer_class = UserOAuthSourceConnectionSerializer


class GroupOAuthSourceConnectionSerializer(GroupSourceConnectionSerializer):
    class Meta(GroupSourceConnectionSerializer.Meta):
        model = GroupOAuthSourceConnection


class GroupOAuthSourceConnectionViewSet(GroupSourceConnectionViewSet, ModelViewSet):
    queryset = GroupOAuthSourceConnection.objects.all()
    serializer_class = GroupOAuthSourceConnectionSerializer
