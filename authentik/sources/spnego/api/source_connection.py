"""SPNEGO Source Serializer"""
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import ModelViewSet

from authentik.api.authorization import OwnerFilter, OwnerSuperuserPermissions
from authentik.core.api.sources import UserSourceConnectionSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.sources.spnego.models import UserSPNEGOSourceConnection


class UserSPNEGOSourceConnectionSerializer(UserSourceConnectionSerializer):
    """SPNEGO Source Serializer"""

    class Meta:
        model = UserSPNEGOSourceConnection
        fields = ["pk", "user", "source", "identifier"]


class UserSPNEGOSourceConnectionViewSet(UsedByMixin, ModelViewSet):
    """Source Viewset"""

    queryset = UserSPNEGOSourceConnection.objects.all()
    serializer_class = UserSPNEGOSourceConnectionSerializer
    filterset_fields = ["source__slug"]
    search_fields = ["source__slug"]
    permission_classes = [OwnerSuperuserPermissions]
    filter_backends = [OwnerFilter, DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering = ["source__slug"]
