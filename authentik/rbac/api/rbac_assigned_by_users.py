"""common RBAC serializers"""
from django.db.models import Q, QuerySet
from django.db.transaction import atomic
from django_filters.filters import CharFilter, ChoiceFilter
from django_filters.filterset import FilterSet
from drf_spectacular.utils import OpenApiResponse, extend_schema
from guardian.models import UserObjectPermission
from guardian.shortcuts import assign_perm, remove_perm
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.fields import BooleanField, ReadOnlyField
from rest_framework.mixins import ListModelMixin
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import GenericViewSet

from authentik.api.decorators import permission_required
from authentik.core.api.groups import GroupMemberSerializer
from authentik.core.models import User, UserTypes
from authentik.policies.event_matcher.models import model_choices
from authentik.rbac.api.rbac import PermissionAssignSerializer


class UserObjectPermissionSerializer(ModelSerializer):
    """User-bound object level permission"""

    app_label = ReadOnlyField(source="content_type.app_label")
    model = ReadOnlyField(source="content_type.model")
    codename = ReadOnlyField(source="permission.codename")
    name = ReadOnlyField(source="permission.name")
    object_pk = ReadOnlyField()

    class Meta:
        model = UserObjectPermission
        fields = ["id", "codename", "model", "app_label", "object_pk", "name"]


class UserAssignedObjectPermissionSerializer(GroupMemberSerializer):
    """Users assigned object permission serializer"""

    permissions = UserObjectPermissionSerializer(many=True, source="userobjectpermission_set")
    is_superuser = BooleanField()

    class Meta:
        model = GroupMemberSerializer.Meta.model
        fields = GroupMemberSerializer.Meta.fields + ["permissions", "is_superuser"]


class UserAssignedPermissionFilter(FilterSet):
    """Assigned permission filter"""

    model = ChoiceFilter(choices=model_choices(), method="filter_model", required=True)
    object_pk = CharFilter(method="filter_object_pk")

    def filter_model(self, queryset: QuerySet, name, value: str) -> QuerySet:
        """Filter by object type"""
        app, _, model = value.partition(".")
        return queryset.filter(
            Q(
                user_permissions__content_type__app_label=app,
                user_permissions__content_type__model=model,
            )
            | Q(
                userobjectpermission__permission__content_type__app_label=app,
                userobjectpermission__permission__content_type__model=model,
            )
            | Q(ak_groups__is_superuser=True)
        ).distinct()

    def filter_object_pk(self, queryset: QuerySet, name, value: str) -> QuerySet:
        """Filter by object primary key"""
        return queryset.filter(
            Q(userobjectpermission__object_pk=value) | Q(ak_groups__is_superuser=True),
        ).distinct()


class UserAssignedPermissionViewSet(ListModelMixin, GenericViewSet):
    """Get assigned object permissions for a single object"""

    serializer_class = UserAssignedObjectPermissionSerializer
    ordering = ["username"]
    # The filtering is done in the filterset,
    # which has a required filter that does the heavy lifting
    queryset = User.objects.all()
    filterset_class = UserAssignedPermissionFilter

    @permission_required("authentik_core.assign_user_permissions")
    @extend_schema(
        request=PermissionAssignSerializer(),
        responses={
            204: OpenApiResponse(description="Successfully assigned"),
        },
    )
    @action(methods=["POST"], detail=True, pagination_class=None, filter_backends=[])
    def assign(self, request: Request, *args, **kwargs) -> Response:
        """Assign permission(s) to user"""
        user: User = self.get_object()
        if user.type == UserTypes.INTERNAL_SERVICE_ACCOUNT:
            raise ValidationError("Permissions cannot be assigned to an internal service account.")
        data = PermissionAssignSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        with atomic():
            for perm in data.validated_data["permissions"]:
                assign_perm(perm, user, data.validated_data["model_instance"])
        return Response(status=204)

    @permission_required("authentik_core.unassign_user_permissions")
    @extend_schema(
        request=PermissionAssignSerializer(),
        responses={
            204: OpenApiResponse(description="Successfully unassigned"),
        },
    )
    @action(methods=["PATCH"], detail=True, pagination_class=None, filter_backends=[])
    def unassign(self, request: Request, *args, **kwargs) -> Response:
        """Unassign permission(s) to user. When `object_pk` is set, the permissions
        are only assigned to the specific object, otherwise they are assigned globally."""
        user: User = self.get_object()
        if user.type == UserTypes.INTERNAL_SERVICE_ACCOUNT:
            raise ValidationError(
                "Permissions cannot be unassigned from an internal service account."
            )
        data = PermissionAssignSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        with atomic():
            for perm in data.validated_data["permissions"]:
                remove_perm(perm, user, data.validated_data["model_instance"])
        return Response(status=204)
