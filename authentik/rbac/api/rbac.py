"""common RBAC serializers"""

from django.apps import apps
from django.contrib.auth.models import Permission
from django.db.models import QuerySet
from django_filters.filters import ModelChoiceFilter
from django_filters.filterset import FilterSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.fields import (
    ReadOnlyField,
    SerializerMethodField,
)
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from authentik.core.api.utils import ModelSerializer
from authentik.rbac.models import Role


class PermissionSerializer(ModelSerializer):
    """Global permission"""

    app_label = ReadOnlyField(source="content_type.app_label")
    app_label_verbose = SerializerMethodField()
    model = ReadOnlyField(source="content_type.model")
    model_verbose = SerializerMethodField()

    def get_app_label_verbose(self, instance: Permission) -> str:
        """Human-readable app label"""
        try:
            return apps.get_app_config(instance.content_type.app_label).verbose_name
        except LookupError:
            return f"{instance.content_type.app_label}.{instance.content_type.model}"

    def get_model_verbose(self, instance: Permission) -> str:
        """Human-readable model name"""
        try:
            return apps.get_model(
                instance.content_type.app_label, instance.content_type.model
            )._meta.verbose_name
        except LookupError:
            return f"{instance.content_type.app_label}.{instance.content_type.model}"

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

    def filter_role(self, queryset: QuerySet, name, value: Role) -> QuerySet:
        """Filter permissions based on role"""
        return queryset.filter(rolemodelpermission__role=value)

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

    queryset = Permission.objects.none()
    serializer_class = PermissionSerializer
    ordering = ["name"]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = PermissionFilter
    permission_classes = [IsAuthenticated]
    search_fields = [
        "name",
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
