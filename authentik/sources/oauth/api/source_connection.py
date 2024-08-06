"""OAuth Source Serializer"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.sources import (
    UserSourceConnectionSerializer,
    UserSourceConnectionViewSet,
)
from authentik.sources.oauth.models import UserOAuthSourceConnection


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
