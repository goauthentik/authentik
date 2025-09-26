"""common RBAC serializers"""

from django.contrib.auth.models import Permission, Group as DjangoGroup
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
from rest_framework.viewsets import GenericViewSet

from authentik.core.api.utils import ModelSerializer, PassiveSerializer
from authentik.policies.event_matcher.models import model_choices
from authentik.rbac.api.rbac import PermissionAssignResultSerializer, PermissionAssignSerializer
from authentik.rbac.decorators import permission_required
from authentik.rbac.models import Role


class RoleObjectPermissionSerializer(ModelSerializer):
    """Role-bound object level permission"""

    app_label = ReadOnlyField(source="content_type.app_label")
    model = ReadOnlyField(source="content_type.model")
    codename = ReadOnlyField(source="permission.codename")
    name = ReadOnlyField(source="permission.name")
    object_pk = CharField()

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

    def filter_queryset(self, queryset: QuerySet[Role]) -> QuerySet[Role]:
        queryset = super().filter_queryset(queryset)
        data = self.form.cleaned_data
        model: str = data["model"]
        object_pk: str | None = data.get("object_pk", None)
        app, _, model = model.partition(".")

        permissions = Permission.objects.filter(
            content_type__app_label=app,
            content_type__model=model,
        )

        group_pks_with_model_permission = (
            permissions.order_by().values_list("group", flat=True).distinct()
        )
        group_pks_with_object_permission = []
        if object_pk:
            group_pks_with_object_permission = (
                GroupObjectPermission.objects.filter(
                    permission__in=permissions, object_pk=object_pk
                )
                .order_by()
                .values_list("group", flat=True)
                .distinct()
            )

        return queryset.filter(
            Q(group_id__in=group_pks_with_model_permission)
            | Q(group_id__in=group_pks_with_object_permission)
        )

    def filter_model(self, queryset: QuerySet, name, value: str) -> QuerySet:
        """Filter by object type"""
        # Actual filtering is handled by the above method where both `model` and `object_pk` are
        # available. Don't do anything here, this method is only left here to avoid overriding too
        # much of filter_queryset.
        return queryset

    def filter_object_pk(self, queryset: QuerySet, name, value: str) -> QuerySet:
        """Filter by object primary key"""
        # Actual filtering is handled by the above method where both `model` and `object_pk` are
        # available. Don't do anything here, this method is only left here to avoid overriding too
        # much of filter_queryset.
        return queryset


class RoleAssignedPermissionViewSet(ListModelMixin, GenericViewSet):
    """Get assigned object permissions for a single object"""

    serializer_class = RoleAssignedObjectPermissionSerializer
    ordering = ["name"]
    # The filtering is done in the filterset,
    # which has a required filter that does the heavy lifting
    queryset = (
        Role.objects.all()
        .select_related("group")
        .prefetch_related("group__groupobjectpermission_set")
    )
    filterset_class = RoleAssignedPermissionFilter

    @permission_required("authentik_rbac.assign_role_permissions")
    @extend_schema(
        request=PermissionAssignSerializer(),
        responses={
            200: PermissionAssignResultSerializer(many=True),
        },
        operation_id="rbac_permissions_assigned_by_roles_assign",
    )
    @action(methods=["POST"], detail=True, pagination_class=None, filter_backends=[])
    def assign(self, request: Request, *args, **kwargs) -> Response:
        """Assign permission(s) to role. When `object_pk` is set, the permissions
        are only assigned to the specific object, otherwise they are assigned globally."""
        role: Role = self.get_object()
        data = PermissionAssignSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        ids = []
        with atomic():
            for perm in data.validated_data["permissions"]:
                assigned_perm = assign_perm(perm, role.group, data.validated_data["model_instance"])
                ids.append(PermissionAssignResultSerializer(instance={"id": assigned_perm.pk}).data)
        return Response(ids, status=200)

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
