"""RBAC Initial Permissions"""

from rest_framework.serializers import ListSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.rbac.api.rbac import PermissionSerializer
from authentik.rbac.models import InitialPermissions


class InitialPermissionsSerializer(ModelSerializer):
    """InitialPermissions serializer"""

    permissions_obj = ListSerializer(
        child=PermissionSerializer(),
        read_only=True,
        source="permissions",
        required=False,
    )

    class Meta:
        model = InitialPermissions
        fields = [
            "pk",
            "name",
            "mode",
            "role",
            "permissions",
            "permissions_obj",
        ]


class InitialPermissionsViewSet(UsedByMixin, ModelViewSet):
    """InitialPermissions viewset"""

    queryset = InitialPermissions.objects.all()
    serializer_class = InitialPermissionsSerializer
    search_fields = ["name"]
    ordering = ["name"]
    filterset_fields = ["name"]
