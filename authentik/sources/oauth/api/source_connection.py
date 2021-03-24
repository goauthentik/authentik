"""OAuth Source Serializer"""
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.sources import SourceSerializer
from authentik.sources.oauth.models import UserOAuthSourceConnection


class UserOAuthSourceConnectionSerializer(SourceSerializer):
    """OAuth Source Serializer"""

    class Meta:
        model = UserOAuthSourceConnection
        fields = [
            "user",
            "source",
            "identifier",
            "access_token",
        ]


class UserOAuthSourceConnectionViewSet(ModelViewSet):
    """Source Viewset"""

    queryset = UserOAuthSourceConnection.objects.all()
    serializer_class = UserOAuthSourceConnectionSerializer

    def get_queryset(self):
        if not self.request:
            return super().get_queryset()
        if self.request.user.is_superuser:
            return super().get_queryset()
        return super().get_queryset().filter(user=self.request.user)
