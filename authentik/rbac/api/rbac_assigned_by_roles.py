"""common RBAC serializers"""
from django.db.models import Q, QuerySet
from django.db.transaction import atomic
from django_filters.filters import CharFilter, ChoiceFilter
from django_filters.filterset import FilterSet
from drf_spectacular.utils import OpenApiResponse, extend_schema
from guardian.models import GroupObjectPermission
from guardian.shortcuts import assign_perm, remove_perm
from rest_framework.decorators import action
from rest_framework.fields import CharField, ReadOnlyField
from rest_framework.mixins import ListModelMixin
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import GenericViewSet

from authentik.api.decorators import permission_required
from authentik.core.api.utils import PassiveSerializer
from authentik.policies.event_matcher.models import model_choices
from authentik.rbac.api.rbac import PermissionAssignSerializer
from authentik.rbac.models import Role


class RoleObjectPermissionSerializer(ModelSerializer):
    """Role-bound object level permission"""

    app_label = ReadOnlyField(source="content_type.app_label")
    model = ReadOnlyField(source="content_type.model")
    codename = ReadOnlyField(source="permission.codename")
    name = ReadOnlyField(source="permission.name")
    object_pk = ReadOnlyField()

    class Meta:
        model = GroupObjectPermission
        fields = ["id", "codename", "model", "app_label", "object_pk", "name"]


class RoleAssignedObjectPermissionSerializer(PassiveSerializer):
    """Roles assigned object permission serializer"""

    role_pk = CharField(source="group.role.pk", read_only=True)
    name = CharField(source="group.name", read_only=True)
    permissions = RoleObjectPermissionSerializer(
        many=True, source="group.groupobjectpermission_set"
    )

    class Meta:
        model = Role
        fields = ["role_pk", "name", "permissions"]


class RoleAssignedPermissionFilter(FilterSet):
    """Role Assigned permission filter"""

    model = ChoiceFilter(choices=model_choices(), method="filter_model", required=True)
    object_pk = CharFilter(method="filter_object_pk")

    def filter_model(self, queryset: QuerySet, name, value: str) -> QuerySet:
        """Filter by object type"""
        app, _, model = value.partition(".")
        return queryset.filter(
            Q(
                group__permissions__content_type__app_label=app,
                group__permissions__content_type__model=model,
            )
            | Q(
                group__groupobjectpermission__permission__content_type__app_label=app,
                group__groupobjectpermission__permission__content_type__model=model,
            )
        ).distinct()

    def filter_object_pk(self, queryset: QuerySet, name, value: str) -> QuerySet:
        """Filter by object primary key"""
        return queryset.filter(Q(group__groupobjectpermission__object_pk=value)).distinct()


class RoleAssignedPermissionViewSet(ListModelMixin, GenericViewSet):
    """Get assigned object permissions for a single object"""

    serializer_class = RoleAssignedObjectPermissionSerializer
    ordering = ["name"]
    # The filtering is done in the filterset,
    # which has a required filter that does the heavy lifting
    queryset = Role.objects.all()
    filterset_class = RoleAssignedPermissionFilter

    @permission_required("authentik_rbac.assign_role_permissions")
    @extend_schema(
        request=PermissionAssignSerializer(),
        responses={
            204: OpenApiResponse(description="Successfully assigned"),
        },
    )
    @action(methods=["POST"], detail=True, pagination_class=None, filter_backends=[])
    def assign(self, request: Request, *args, **kwargs) -> Response:
        """Assign permission(s) to role. When `object_pk` is set, the permissions
        are only assigned to the specific object, otherwise they are assigned globally."""
        role: Role = self.get_object()
        data = PermissionAssignSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        with atomic():
            for perm in data.validated_data["permissions"]:
                assign_perm(perm, role.group, data.validated_data["model_instance"])
        return Response(status=204)

    @permission_required("authentik_rbac.unassign_role_permissions")
    @extend_schema(
        request=PermissionAssignSerializer(),
        responses={
            204: OpenApiResponse(description="Successfully unassigned"),
        },
    )
    @action(methods=["PATCH"], detail=True, pagination_class=None, filter_backends=[])
    def unassign(self, request: Request, *args, **kwargs) -> Response:
        """Unassign permission(s) to role. When `object_pk` is set, the permissions
        are only assigned to the specific object, otherwise they are assigned globally."""
        role: Role = self.get_object()
        data = PermissionAssignSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        with atomic():
            for perm in data.validated_data["permissions"]:
                remove_perm(perm, role.group, data.validated_data["model_instance"])
        return Response(status=204)
