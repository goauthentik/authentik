"""RBAC Roles"""

from django.contrib.auth.models import Permission
from rest_framework.fields import (
    ChoiceField,
    ListField,
)
from rest_framework.viewsets import ModelViewSet

from authentik.blueprints.v1.importer import SERIALIZER_CONTEXT_BLUEPRINT
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.rbac.models import Role, get_permission_choices


class RoleSerializer(ModelSerializer):
    """Role serializer"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if SERIALIZER_CONTEXT_BLUEPRINT in self.context:
            self.fields["permissions"] = ListField(
                required=False, child=ChoiceField(choices=get_permission_choices())
            )

    def create(self, validated_data: dict) -> Role:
        perms_qs = Permission.objects.filter(
            codename__in=[x.split(".")[1] for x in validated_data.pop("permissions", [])]
        ).values_list("content_type__app_label", "codename")
        perms_list = [f"{ct}.{name}" for ct, name in list(perms_qs)]

        instance: Role = super().create(validated_data)
        instance.assign_perms(perms_list)

        return instance

    def update(self, instance: Role, validated_data: dict) -> Role:
        perms_qs = Permission.objects.filter(
            codename__in=[x.split(".")[1] for x in validated_data.pop("permissions", [])]
        ).values_list("content_type__app_label", "codename")
        perms_list = [f"{ct}.{name}" for ct, name in list(perms_qs)]

        instance: Role = super().update(instance, validated_data)
        instance.assign_perms(perms_list)

        return instance

    class Meta:
        model = Role
        fields = ["pk", "name"]


class RoleViewSet(UsedByMixin, ModelViewSet):
    """Role viewset"""

    serializer_class = RoleSerializer
    queryset = Role.objects.all()
    search_fields = ["name"]
    ordering = ["name"]
    filterset_fields = ["name"]
