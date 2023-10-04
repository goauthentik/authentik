"""common RBAC serializers"""
from django.apps import apps
from django.contrib.auth.models import Permission
from django.db.models import QuerySet
from django_filters.filters import ModelChoiceFilter
from django_filters.filterset import FilterSet
from guardian.models import GroupObjectPermission, UserObjectPermission
from rest_framework.fields import (
    CharField,
    ChoiceField,
    ListField,
    ReadOnlyField,
    SerializerMethodField,
)
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ReadOnlyModelViewSet

from authentik.core.api.utils import PassiveSerializer
from authentik.core.models import Role
from authentik.lib.validators import RequiredTogetherValidator
from authentik.policies.event_matcher.models import model_choices


class PermissionSerializer(ModelSerializer):
    """Global permission"""

    app_label = ReadOnlyField(source="content_type.app_label")
    app_label_verbose = SerializerMethodField()
    model = ReadOnlyField(source="content_type.model")

    def get_app_label_verbose(self, instance: Permission) -> str:
        return apps.get_app_config(instance.content_type.app_label).verbose_name

    class Meta:
        model = Permission
        fields = ["id", "name", "codename", "model", "app_label", "app_label_verbose"]


class UserObjectPermissionSerializer(ModelSerializer):
    """User-bound object level permission"""

    app_label = ReadOnlyField(source="content_type.app_label")
    model = ReadOnlyField(source="content_type.model")
    codename = ReadOnlyField(source="permission.codename")

    class Meta:
        model = UserObjectPermission
        fields = ["id", "codename", "model", "app_label"]


class RoleObjectPermissionSerializer(ModelSerializer):
    """Role-bound object level permission"""

    app_label = ReadOnlyField(source="content_type.app_label")
    model = ReadOnlyField(source="content_type.model")
    codename = ReadOnlyField(source="permission.codename")

    class Meta:
        model = GroupObjectPermission
        fields = ["id", "codename", "model", "app_label"]


class PermissionFilter(FilterSet):
    """Filter permissions"""

    role = ModelChoiceFilter(queryset=Role.objects.all(), method="filter_role")

    def filter_role(self, queryset: QuerySet, name, value: Role) -> QuerySet:
        """Filter permissions based on role"""
        return queryset.filter(group__role=value)

    class Meta:
        model = Permission
        fields = [
            "codename",
            "content_type__model",
            "content_type__app_label",
            "role",
        ]


class RBACPermissionViewSet(ReadOnlyModelViewSet):
    """Read-only list of all permissions, filterable by model and app"""

    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    ordering = ["name"]
    filterset_class = PermissionFilter
    search_fields = [
        "codename",
        "content_type__model",
        "content_type__app_label",
    ]


class PermissionAssignSerializer(PassiveSerializer):
    """Request to assign a new permission"""

    permissions = ListField(child=CharField())
    model = ChoiceField(choices=model_choices(), required=False)
    object_pk = CharField(required=False)

    validators = [RequiredTogetherValidator(fields=["model", "object_pk"])]
