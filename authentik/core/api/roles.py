"""RBAC Roles"""
from rest_framework.fields import CharField
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet
from authentik.core.api.used_by import UsedByMixin

from authentik.core.models import Role


class RoleSerializer(ModelSerializer):
    """Role serializer"""
    name = CharField(source="group.name")

    def create(self, validated_data):
        print(validated_data)
        return super().create(validated_data)

    class Meta:
        model = Role
        fields = ["pk", "name"]


class RoleViewSet(UsedByMixin, ModelViewSet):
    """Role viewset"""

    serializer_class = RoleSerializer
    queryset = Role.objects.all()
    search_fields = ["group__name"]
    ordering = ["group__name"]
