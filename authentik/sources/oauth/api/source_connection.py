"""OAuth Source Serializer"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import ModelViewSet

from authentik.api.authorization import OwnerFilter, OwnerSuperuserPermissions
from authentik.core.api.sources import GroupSourceConnectionSerializer, GroupSourceConnectionViewSet, UserSourceConnectionSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.sources.oauth.models import GroupOAuthSourceConnection, UserOAuthSourceConnection


class UserOAuthSourceConnectionSerializer(UserSourceConnectionSerializer):
    """OAuth Source Serializer"""

    class Meta:
        model = UserOAuthSourceConnection
        fields = ["pk", "user", "source", "identifier", "access_token"]
        extra_kwargs = {
            "access_token": {"write_only": True},
        }


class UserOAuthSourceConnectionViewSet(UsedByMixin, ModelViewSet):
    """Source Viewset"""

    queryset = UserOAuthSourceConnection.objects.all()
    serializer_class = UserOAuthSourceConnectionSerializer
    filterset_fields = ["source__slug"]
    search_fields = ["source__slug"]
    permission_classes = [OwnerSuperuserPermissions]
    filter_backends = [OwnerFilter, DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering = ["source__slug"]


class GroupOAuthSourceConnectionSerializer(GroupSourceConnectionSerializer):
    """OAuth Group-Source connection Serializer"""

    class Meta(GroupSourceConnectionSerializer.Meta):
        model = GroupOAuthSourceConnection


class GroupOAuthSourceConnectionViewSet(GroupSourceConnectionViewSet):
    """Group-source connection Viewset"""

    queryset = GroupOAuthSourceConnection.objects.all()
    serializer_class = GroupOAuthSourceConnectionSerializer
