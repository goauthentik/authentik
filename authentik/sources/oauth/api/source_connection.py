"""OAuth Source Serializer"""
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.sources import SourceSerializer
from authentik.sources.oauth.models import UserOAuthSourceConnection


class UserOAuthSourceConnectionSerializer(SourceSerializer):
    """OAuth Source Serializer"""

    class Meta:
        model = UserOAuthSourceConnection
        fields = [
            "pk",
            "user",
            "source",
            "identifier",
        ]


class UserOAuthSourceConnectionViewSet(ModelViewSet):
    """Source Viewset"""

    queryset = UserOAuthSourceConnection.objects.all()
    serializer_class = UserOAuthSourceConnectionSerializer
    filterset_fields = ["source__slug"]

    def get_queryset(self):
        if not self.request:
            return super().get_queryset()
        if self.request.user.is_superuser:
            return super().get_queryset()
        return super().get_queryset().filter(user=self.request.user)
