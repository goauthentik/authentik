"""RBAC Roles"""
from rest_framework.fields import CharField
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.core.models import Role


class RoleSerializer(ModelSerializer):
    name = CharField(source="group.name")

    def create(self, validated_data):
        return super().create(validated_data)

    class Meta:
        model = Role
        fields = ["name"]


class RoleViewSet(ModelViewSet):
    queryset = Role.objects.all()
    search_fields = ["group__name"]
    ordering = ["group__name"]
