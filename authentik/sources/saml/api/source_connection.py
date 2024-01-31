"""SAML Source Serializer"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import ModelViewSet

from authentik.api.authorization import OwnerFilter, OwnerSuperuserPermissions
from authentik.core.api.sources import UserSourceConnectionSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.sources.saml.models import UserSAMLSourceConnection


class UserSAMLSourceConnectionSerializer(UserSourceConnectionSerializer):
    """SAML Source Serializer"""

    class Meta:
        model = UserSAMLSourceConnection
        fields = ["pk", "user", "source", "identifier"]


class UserSAMLSourceConnectionViewSet(UsedByMixin, ModelViewSet):
    """Source Viewset"""

    queryset = UserSAMLSourceConnection.objects.all()
    serializer_class = UserSAMLSourceConnectionSerializer
    filterset_fields = ["source__slug"]
    search_fields = ["source__slug"]
    permission_classes = [OwnerSuperuserPermissions]
    filter_backends = [OwnerFilter, DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering = ["source__slug"]
