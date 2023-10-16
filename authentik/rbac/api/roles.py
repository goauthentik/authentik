"""RBAC Roles"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.rbac.models import Role


class RoleSerializer(ModelSerializer):
    """Role serializer"""

    class Meta:
        model = Role
        fields = ["pk", "name"]


class RoleViewSet(UsedByMixin, ModelViewSet):
    """Role viewset"""

    serializer_class = RoleSerializer
    queryset = Role.objects.all()
    search_fields = ["group__name"]
    ordering = ["group__name"]
    filterset_fields = ["group__name"]
