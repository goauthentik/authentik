"""RBAC Roles"""
from django.contrib.auth.models import Group
from rest_framework.fields import CharField
from rest_framework.serializers import ModelSerializer
from rest_framework.validators import UniqueValidator
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.models import Role


class RoleSerializer(ModelSerializer):
    """Role serializer"""

    name = CharField(
        source="group.name",
        max_length=150,
        validators=[UniqueValidator(queryset=Group.objects.all())],
    )

    def create(self, validated_data: dict):
        name = validated_data["group"]["name"]
        group = Group.objects.create(name=name)
        return super().create({"group": group})

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
