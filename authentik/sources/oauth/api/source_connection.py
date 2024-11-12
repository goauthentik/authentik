"""OAuth Source Serializer"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.sources import (
    GroupSourceConnectionSerializer,
    GroupSourceConnectionViewSet,
    UserSourceConnectionSerializer,
    UserSourceConnectionViewSet,
)
from authentik.sources.oauth.models import GroupOAuthSourceConnection, UserOAuthSourceConnection


class UserOAuthSourceConnectionSerializer(UserSourceConnectionSerializer):
    """OAuth Source Serializer"""

    class Meta(UserSourceConnectionSerializer.Meta):
        model = UserOAuthSourceConnection
        fields = UserSourceConnectionSerializer.Meta.fields + ["identifier", "access_token"]
        extra_kwargs = {
            **UserSourceConnectionSerializer.Meta.extra_kwargs,
            "access_token": {"write_only": True},
        }


class UserOAuthSourceConnectionViewSet(UserSourceConnectionViewSet, ModelViewSet):
    """Source Viewset"""

    queryset = UserOAuthSourceConnection.objects.all()
    serializer_class = UserOAuthSourceConnectionSerializer


class GroupOAuthSourceConnectionSerializer(GroupSourceConnectionSerializer):
    """OAuth Group-Source connection Serializer"""

    class Meta(GroupSourceConnectionSerializer.Meta):
        model = GroupOAuthSourceConnection


class GroupOAuthSourceConnectionViewSet(GroupSourceConnectionViewSet, ModelViewSet):
    """Group-source connection Viewset"""

    queryset = GroupOAuthSourceConnection.objects.all()
    serializer_class = GroupOAuthSourceConnectionSerializer
