"""Groups API Viewset"""

from json import loads

from django.db.models import Prefetch
from django.http import Http404
from django.utils.translation import gettext as _
from django_filters.filters import CharFilter, ModelMultipleChoiceFilter
from django_filters.filterset import FilterSet
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_field,
)
from guardian.shortcuts import get_objects_for_user
from rest_framework.decorators import action
from rest_framework.fields import CharField, IntegerField, SerializerMethodField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ListSerializer, ValidationError
from rest_framework.validators import UniqueValidator
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import JSONDictField, ModelSerializer, PassiveSerializer
from authentik.core.models import Group, User
from authentik.rbac.api.roles import RoleSerializer
from authentik.rbac.decorators import permission_required


class GroupMemberSerializer(ModelSerializer):
    """Stripped down user serializer to show relevant users for groups"""

    attributes = JSONDictField(required=False)
    uid = CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "pk",
            "username",
            "name",
            "is_active",
            "last_login",
            "email",
            "attributes",
            "uid",
        ]


class GroupSerializer(ModelSerializer):
    """Group Serializer"""

    attributes = JSONDictField(required=False)
    users_obj = SerializerMethodField(allow_null=True)
    roles_obj = ListSerializer(
        child=RoleSerializer(),
        read_only=True,
        source="roles",
        required=False,
    )
    parent_name = CharField(source="parent.name", read_only=True, allow_null=True)

    num_pk = IntegerField(read_only=True)

    @property
    def _should_include_users(self) -> bool:
        request: Request = self.context.get("request", None)
        if not request:
            return True
        return str(request.query_params.get("include_users", "true")).lower() == "true"

    @extend_schema_field(GroupMemberSerializer(many=True))
    def get_users_obj(self, instance: Group) -> list[GroupMemberSerializer] | None:
        if not self._should_include_users:
            return None
        return GroupMemberSerializer(instance.users, many=True).data

    def validate_parent(self, parent: Group | None):
        """Validate group parent (if set), ensuring the parent isn't itself"""
        if not self.instance or not parent:
            return parent
        if str(parent.group_uuid) == str(self.instance.group_uuid):
            raise ValidationError(_("Cannot set group as parent of itself."))
        return parent

    def validate_is_superuser(self, superuser: bool):
        """Ensure that the user creating this group has permissions to set the superuser flag"""
        request: Request = self.context.get("request", None)
        if not request:
            return superuser
        # If we're updating an instance, and the state hasn't changed, we don't need to check perms
        if self.instance and superuser == self.instance.is_superuser:
            return superuser
        user: User = request.user
        perm = (
            "authentik_core.enable_group_superuser"
            if superuser
            else "authentik_core.disable_group_superuser"
        )
        if self.instance or superuser:
            has_perm = user.has_perm(perm) or user.has_perm(perm, self.instance)
            if not has_perm:
                raise ValidationError(
                    _(
                        (
                            "User does not have permission to set "
                            "superuser status to {superuser_status}."
                        ).format_map({"superuser_status": superuser})
                    )
                )
        return superuser

    class Meta:
        model = Group
        fields = [
            "pk",
            "num_pk",
            "name",
            "is_superuser",
            "parent",
            "parent_name",
            "users",
            "users_obj",
            "attributes",
            "roles",
            "roles_obj",
        ]
        extra_kwargs = {
            "users": {
                "default": list,
            },
            # TODO: This field isn't unique on the database which is hard to backport
            # hence we just validate the uniqueness here
            "name": {"validators": [UniqueValidator(Group.objects.all())]},
        }


class GroupFilter(FilterSet):
    """Filter for groups"""

    attributes = CharFilter(
        field_name="attributes",
        lookup_expr="",
        label="Attributes",
        method="filter_attributes",
    )

    members_by_username = ModelMultipleChoiceFilter(
        field_name="users__username",
        to_field_name="username",
        queryset=User.objects.all(),
    )
    members_by_pk = ModelMultipleChoiceFilter(
        field_name="users",
        queryset=User.objects.all(),
    )

    def filter_attributes(self, queryset, name, value):
        """Filter attributes by query args"""
        try:
            value = loads(value)
        except ValueError:
            raise ValidationError(detail="filter: failed to parse JSON") from None
        if not isinstance(value, dict):
            raise ValidationError(detail="filter: value must be key:value mapping")
        qs = {}
        for key, _value in value.items():
            qs[f"attributes__{key}"] = _value
        try:
            _ = len(queryset.filter(**qs))
            return queryset.filter(**qs)
        except ValueError:
            return queryset

    class Meta:
        model = Group
        fields = ["name", "is_superuser", "members_by_pk", "attributes", "members_by_username"]


class GroupViewSet(UsedByMixin, ModelViewSet):
    """Group Viewset"""

    class UserAccountSerializer(PassiveSerializer):
        """Account adding/removing operations"""

        pk = IntegerField(required=True)

    queryset = Group.objects.none()
    serializer_class = GroupSerializer
    search_fields = ["name", "is_superuser"]
    filterset_class = GroupFilter
    ordering = ["name"]

    def get_queryset(self):
        base_qs = Group.objects.all().select_related("parent").prefetch_related("roles")

        if self.serializer_class(context={"request": self.request})._should_include_users:
            base_qs = base_qs.prefetch_related("users")
        else:
            base_qs = base_qs.prefetch_related(
                Prefetch("users", queryset=User.objects.all().only("id"))
            )

        return base_qs

    @extend_schema(
        parameters=[
            OpenApiParameter("include_users", bool, default=True),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("include_users", bool, default=True),
        ]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @permission_required("authentik_core.add_user_to_group")
    @extend_schema(
        request=UserAccountSerializer,
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
        permission_classes=[],
    )
    def add_user(self, request: Request, pk: str) -> Response:
        """Add user to group"""
        group: Group = self.get_object()
        user: User = (
            get_objects_for_user(request.user, "authentik_core.view_user")
            .filter(
                pk=request.data.get("pk"),
            )
            .first()
        )
        if not user:
            raise Http404
        group.users.add(user)
        return Response(status=204)

    @permission_required("authentik_core.remove_user_from_group")
    @extend_schema(
        request=UserAccountSerializer,
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
        permission_classes=[],
    )
    def remove_user(self, request: Request, pk: str) -> Response:
        """Add user to group"""
        group: Group = self.get_object()
        user: User = (
            get_objects_for_user(request.user, "authentik_core.view_user")
            .filter(
                pk=request.data.get("pk"),
            )
            .first()
        )
        if not user:
            raise Http404
        group.users.remove(user)
        return Response(status=204)
