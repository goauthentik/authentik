"""RBAC Roles"""

from django.contrib.auth.models import Permission
from django.http import Http404
from django_filters.filters import AllValuesMultipleFilter, BooleanFilter, CharFilter, NumberFilter
from django_filters.filterset import FilterSet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_field
from guardian.shortcuts import get_objects_for_user
from rest_framework.decorators import action
from rest_framework.fields import (
    ChoiceField,
    IntegerField,
    ListField,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentik.blueprints.api import ManagedSerializer
from authentik.blueprints.v1.importer import SERIALIZER_CONTEXT_BLUEPRINT
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer, PassiveSerializer
from authentik.core.models import Group, User
from authentik.rbac.decorators import permission_required
from authentik.rbac.models import Role, get_permission_choices


class RoleSerializer(ManagedSerializer, ModelSerializer):
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


class RoleFilterSet(FilterSet):
    """Filter for Role"""

    managed = extend_schema_field(OpenApiTypes.STR)(AllValuesMultipleFilter(field_name="managed"))

    managed__isnull = BooleanFilter(field_name="managed", lookup_expr="isnull")

    inherited_user_roles = extend_schema_field(OpenApiTypes.INT)(
        NumberFilter(
            method="filter_inherited_user_roles",
            label="Filter by inherited roles from groups (excludes direct)",
        )
    )

    inherited_group_roles = extend_schema_field(OpenApiTypes.UUID)(
        CharFilter(
            method="filter_inherited_group_roles",
            label="Filter by inherited roles from ancestor groups (excludes direct)",
        )
    )

    def filter_inherited_user_roles(self, queryset, name, value):
        """Filter roles inherited from groups (excludes direct user roles)"""
        try:
            user = User.objects.get(pk=value)
        except User.DoesNotExist:
            return queryset.none()
        direct_role_pks = set(user.roles.values_list("pk", flat=True))
        return user.all_roles().exclude(pk__in=direct_role_pks)

    def filter_inherited_group_roles(self, queryset, name, value):
        """Filter roles inherited from ancestor groups (excludes direct roles)"""
        try:
            group = Group.objects.get(pk=value)
        except Group.DoesNotExist:
            return queryset.none()
        direct_role_pks = set(group.roles.values_list("pk", flat=True))
        return group.all_roles().exclude(pk__in=direct_role_pks)

    class Meta:
        model = Role
        fields = [
            "name",
            "users",
            "ak_groups",
            "managed",
            "inherited_user_roles",
            "inherited_group_roles",
        ]


class RoleViewSet(UsedByMixin, ModelViewSet):
    """Role viewset"""

    serializer_class = RoleSerializer
    queryset = Role.objects.all()
    search_fields = ["name"]
    ordering = ["name"]
    filterset_class = RoleFilterSet

    class UserAccountSerializerForRole(PassiveSerializer):
        """Account adding/removing operations"""

        pk = IntegerField(required=True)

    @permission_required("authentik_rbac.change_role")
    @extend_schema(
        request=UserAccountSerializerForRole,
        responses={
            204: OpenApiResponse(description="User added"),
            404: OpenApiResponse(description="User not found"),
        },
    )
    @action(
        detail=True,
        methods=["POST"],
        pagination_class=None,
        filter_backends=[],
        permission_classes=[IsAuthenticated],
    )
    def add_user(self, request: Request, pk: str) -> Response:
        """Add user to role"""
        role: Role = self.get_object()
        user: User = (
            get_objects_for_user(request.user, "authentik_core.view_user")
            .filter(
                pk=request.data.get("pk"),
            )
            .first()
        )
        if not user:
            raise Http404
        role.users.add(user)
        return Response(status=204)

    @permission_required("authentik_rbac.change_role")
    @extend_schema(
        request=UserAccountSerializerForRole,
        responses={
            204: OpenApiResponse(description="User removed"),
            404: OpenApiResponse(description="User not found"),
        },
    )
    @action(
        detail=True,
        methods=["POST"],
        pagination_class=None,
        filter_backends=[],
        permission_classes=[IsAuthenticated],
    )
    def remove_user(self, request: Request, pk: str) -> Response:
        """Remove user from role"""
        role: Role = self.get_object()
        user: User = (
            get_objects_for_user(request.user, "authentik_core.view_user")
            .filter(
                pk=request.data.get("pk"),
            )
            .first()
        )
        if not user:
            raise Http404
        role.users.remove(user)
        return Response(status=204)
