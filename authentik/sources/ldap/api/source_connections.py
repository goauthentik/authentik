"""LDAP Source Serializer"""
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import ModelViewSet

from authentik.api.authorization import OwnerFilter, OwnerSuperuserPermissions
from authentik.core.api.sources import UserSourceConnectionSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.sources.ldap.models import LDAPUserSourceConnection


class LDAPUserSourceConnectionSerializer(UserSourceConnectionSerializer):
    """LDAP Source Serializer"""

    class Meta:
        model = LDAPUserSourceConnection
        fields = ["pk", "user", "source", "unique_identifier"]
        extra_kwargs = {
            "access_token": {"write_only": True},
        }


class LDAPUserSourceConnectionViewSet(UsedByMixin, ModelViewSet):
    """Source Viewset"""

    queryset = LDAPUserSourceConnection.objects.all()
    serializer_class = LDAPUserSourceConnectionSerializer
    filterset_fields = ["source__slug"]
    search_fields = ["source__slug"]
    permission_classes = [OwnerSuperuserPermissions]
    filter_backends = [OwnerFilter, DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering = ["source__slug"]
