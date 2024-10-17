"""Kerberos Source Serializer"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import ModelViewSet

from authentik.api.authorization import OwnerFilter, OwnerSuperuserPermissions
from authentik.core.api.sources import (
    GroupSourceConnectionSerializer,
    GroupSourceConnectionViewSet,
    UserSourceConnectionSerializer,
)
from authentik.core.api.used_by import UsedByMixin
from authentik.sources.kerberos.models import (
    GroupKerberosSourceConnection,
    UserKerberosSourceConnection,
)


class UserKerberosSourceConnectionSerializer(UserSourceConnectionSerializer):
    """Kerberos Source Serializer"""

    class Meta:
        model = UserKerberosSourceConnection
        fields = UserSourceConnectionSerializer.Meta.fields + ["identifier"]


class UserKerberosSourceConnectionViewSet(UsedByMixin, ModelViewSet):
    """Source Viewset"""

    queryset = UserKerberosSourceConnection.objects.all()
    serializer_class = UserKerberosSourceConnectionSerializer
    filterset_fields = ["source__slug"]
    search_fields = ["source__slug"]
    permission_classes = [OwnerSuperuserPermissions]
    filter_backends = [OwnerFilter, DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering = ["source__slug"]


class GroupKerberosSourceConnectionSerializer(GroupSourceConnectionSerializer):
    """OAuth Group-Source connection Serializer"""

    class Meta(GroupSourceConnectionSerializer.Meta):
        model = GroupKerberosSourceConnection


class GroupKerberosSourceConnectionViewSet(GroupSourceConnectionViewSet):
    """Group-source connection Viewset"""

    queryset = GroupKerberosSourceConnection.objects.all()
    serializer_class = GroupKerberosSourceConnectionSerializer
