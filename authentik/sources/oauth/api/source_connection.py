"""OAuth Source Serializer"""
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import GenericViewSet

from authentik.api.authorization import OwnerFilter, OwnerPermissions
from authentik.core.api.sources import SourceSerializer
from authentik.core.api.used_by import UsedByMixin
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
        extra_kwargs = {
            "user": {"read_only": True},
        }


class UserOAuthSourceConnectionViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """Source Viewset"""

    queryset = UserOAuthSourceConnection.objects.all()
    serializer_class = UserOAuthSourceConnectionSerializer
    filterset_fields = ["source__slug"]
    permission_classes = [OwnerPermissions]
    filter_backends = [OwnerFilter, DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering = ["source__slug"]
