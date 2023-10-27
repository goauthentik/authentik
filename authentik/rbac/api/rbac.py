"""common RBAC serializers"""
from django.apps import apps
from django.contrib.auth.models import Permission
from django.db.models import QuerySet
from django_filters.filters import ModelChoiceFilter
from django_filters.filterset import FilterSet
from rest_framework.exceptions import ValidationError
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
from authentik.core.models import User
from authentik.lib.validators import RequiredTogetherValidator
from authentik.policies.event_matcher.models import model_choices
from authentik.rbac.models import Role


class PermissionSerializer(ModelSerializer):
    """Global permission"""

    app_label = ReadOnlyField(source="content_type.app_label")
    app_label_verbose = SerializerMethodField()
    model = ReadOnlyField(source="content_type.model")
    model_verbose = SerializerMethodField()

    def get_app_label_verbose(self, instance: Permission) -> str:
        """Human-readable app label"""
        return apps.get_app_config(instance.content_type.app_label).verbose_name

    def get_model_verbose(self, instance: Permission) -> str:
        """Human-readable model name"""
        return apps.get_model(
            instance.content_type.app_label, instance.content_type.model
        )._meta.verbose_name

    class Meta:
        model = Permission
        fields = [
            "id",
            "name",
            "codename",
            "model",
            "app_label",
            "app_label_verbose",
            "model_verbose",
        ]


class PermissionFilter(FilterSet):
    """Filter permissions"""

    role = ModelChoiceFilter(queryset=Role.objects.all(), method="filter_role")
    user = ModelChoiceFilter(queryset=User.objects.all())

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
            "user",
        ]


class RBACPermissionViewSet(ReadOnlyModelViewSet):
    """Read-only list of all permissions, filterable by model and app"""

    queryset = Permission.objects.none()
    serializer_class = PermissionSerializer
    ordering = ["name"]
    filterset_class = PermissionFilter
    search_fields = [
        "codename",
        "content_type__model",
        "content_type__app_label",
    ]

    def get_queryset(self) -> QuerySet:
        return (
            Permission.objects.all()
            .select_related("content_type")
            .filter(
                content_type__app_label__startswith="authentik",
            )
        )


class PermissionAssignSerializer(PassiveSerializer):
    """Request to assign a new permission"""

    permissions = ListField(child=CharField())
    model = ChoiceField(choices=model_choices(), required=False)
    object_pk = CharField(required=False)

    validators = [RequiredTogetherValidator(fields=["model", "object_pk"])]

    def validate(self, attrs: dict) -> dict:
        model_instance = None
        # Check if we're setting an object-level perm or global
        model = attrs.get("model")
        object_pk = attrs.get("object_pk")
        if model and object_pk:
            model = apps.get_model(attrs["model"])
            model_instance = model.objects.filter(pk=attrs["object_pk"]).first()
        attrs["model_instance"] = model_instance
        if attrs.get("model"):
            return attrs
        permissions = attrs.get("permissions", [])
        if not all("." in perm for perm in permissions):
            raise ValidationError(
                {
                    "permissions": (
                        "When assigning global permissions, codename must be given as "
                        "app_label.codename"
                    )
                }
            )
        return attrs
