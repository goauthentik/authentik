"""OAuth Source Serializer"""
from django_filters.rest_framework import DjangoFilterBackend
from guardian.utils import get_anonymous_user
from rest_framework.filters import OrderingFilter, SearchFilter
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
    filter_backends = [
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]

    def get_queryset(self):
        user = self.request.user if self.request else get_anonymous_user()
        if user.is_superuser:
            return super().get_queryset()
        return super().get_queryset().filter(user=user.pk)
