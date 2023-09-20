"""common RBAC serializers"""
from django.contrib.auth.models import Permission
from guardian.models import UserObjectPermission, GroupObjectPermission
from rest_framework.fields import ReadOnlyField
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ReadOnlyModelViewSet


class PermissionSerializer(ModelSerializer):
    app_label = ReadOnlyField(source="content_type.app_label")
    model = ReadOnlyField(source="content_type.model")

    class Meta:
        model = Permission
        fields = ["id", "name", "codename", "model", "app_label"]


class UserObjectPermissionSerializer(ModelSerializer):
    app_label = ReadOnlyField(source="content_type.app_label")
    model = ReadOnlyField(source="content_type.model")
    codename = ReadOnlyField(source="permission.codename")

    class Meta:
        model = UserObjectPermission
        fields = ["id", "codename", "model", "app_label"]

class GroupObjectPermissionSerializer(ModelSerializer):
    app_label = ReadOnlyField(source="content_type.app_label")
    model = ReadOnlyField(source="content_type.model")
    codename = ReadOnlyField(source="permission.codename")

    class Meta:
        model = GroupObjectPermission
        fields = ["id", "codename", "model", "app_label"]


class RBACPermissionViewSet(ReadOnlyModelViewSet):
    """Read-only list of all permissions, filterable by model and app"""

    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    ordering = ["name"]
    filterset_fields = ["codename", "content_type__model", "content_type__app_label"]
