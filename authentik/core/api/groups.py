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
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.fields import CharField, IntegerField, SerializerMethodField
from rest_framework.permissions import IsAuthenticated
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ListSerializer, ValidationError
from rest_framework.viewsets import ModelViewSet

from authentik.api.authentication import TokenAuthentication
from authentik.api.validation import validate
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import JSONDictField, ModelSerializer, PassiveSerializer
from authentik.core.models import Group, User
from authentik.endpoints.connectors.agent.auth import AgentAuth
from authentik.rbac.api.roles import RoleSerializer
from authentik.rbac.decorators import permission_required

PARTIAL_USER_SERIALIZER_MODEL_FIELDS = [
    "pk",
    "username",
    "name",
    "is_active",
    "last_login",
    "email",
    "attributes",
]


class PartialUserSerializer(ModelSerializer):
    """Partial User Serializer, does not include child relations."""

    attributes = JSONDictField(required=False)
    uid = CharField(read_only=True)

    class Meta:
        model = User
        fields = PARTIAL_USER_SERIALIZER_MODEL_FIELDS + ["uid"]


class RelatedGroupSerializer(ModelSerializer):
    """Stripped down group serializer to show relevant children/parents for groups"""

    attributes = JSONDictField(required=False)

    class Meta:
        model = Group
        fields = [
            "pk",
            "name",
            "is_superuser",
            "attributes",
            "group_uuid",
        ]


class GroupSerializer(ModelSerializer):
    """Group Serializer"""

    attributes = JSONDictField(required=False)
    parents = PrimaryKeyRelatedField(queryset=Group.objects.all(), many=True, required=False)
    parents_obj = SerializerMethodField(allow_null=True)
    children_obj = SerializerMethodField(allow_null=True)
    users_obj = SerializerMethodField(allow_null=True)
    roles_obj = ListSerializer(
        child=RoleSerializer(),
        read_only=True,
        source="roles",
        required=False,
    )
    inherited_roles_obj = SerializerMethodField(read_only=True)
    num_pk = IntegerField(read_only=True)

    @property
    def _should_include_users(self) -> bool:
        request: Request = self.context.get("request", None)
        if not request:
            return True
        return str(request.query_params.get("include_users", "true")).lower() == "true"

    @property
    def _should_include_children(self) -> bool:
        request: Request = self.context.get("request", None)
        if not request:
            return True
        return str(request.query_params.get("include_children", "false")).lower() == "true"

    @property
    def _should_include_parents(self) -> bool:
        request: Request = self.context.get("request", None)
        if not request:
            return True
        return str(request.query_params.get("include_parents", "false")).lower() == "true"

    @extend_schema_field(PartialUserSerializer(many=True))
    def get_users_obj(self, instance: Group) -> list[PartialUserSerializer] | None:
        if not self._should_include_users:
            return None
        return PartialUserSerializer(instance.users, many=True).data

    @extend_schema_field(RelatedGroupSerializer(many=True))
    def get_children_obj(self, instance: Group) -> list[RelatedGroupSerializer] | None:
        if not self._should_include_children:
            return None
        return RelatedGroupSerializer(instance.children, many=True).data

    @extend_schema_field(RelatedGroupSerializer(many=True))
    def get_parents_obj(self, instance: Group) -> list[RelatedGroupSerializer] | None:
        if not self._should_include_parents:
            return None
        return RelatedGroupSerializer(instance.parents, many=True).data

    @extend_schema_field(RoleSerializer(many=True))
    def get_inherited_roles_obj(self, instance: Group) -> list:
        """Return only inherited roles from ancestor groups (excludes direct roles)"""
        direct_role_pks = set(instance.roles.values_list("pk", flat=True))
        inherited_roles = instance.all_roles().exclude(pk__in=direct_role_pks)
        return RoleSerializer(inherited_roles, many=True).data

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
            "parents",
            "parents_obj",
            "users",
            "users_obj",
            "attributes",
            "roles",
            "roles_obj",
            "inherited_roles_obj",
            "children",
            "children_obj",
        ]
        extra_kwargs = {
            "users": {
                "default": list,
            },
            "children": {
                "required": False,
                "default": list,
            },
            "parents": {
                "required": False,
                "default": list,
            },
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
    authentication_classes = [
        TokenAuthentication,
        SessionAuthentication,
        AgentAuth,
    ]

    def get_ql_fields(self):
        from djangoql.schema import BoolField, StrField

        from authentik.enterprise.search.fields import (
            JSONSearchField,
        )

        return [
            StrField(Group, "name"),
            BoolField(Group, "is_superuser", nullable=True),
            JSONSearchField(Group, "attributes"),
        ]

    def get_queryset(self):
        base_qs = Group.objects.all().prefetch_related("roles")

        if self.serializer_class(context={"request": self.request})._should_include_users:
            # Only fetch fields needed by PartialUserSerializer to reduce DB load and instantiation
            # time
            base_qs = base_qs.prefetch_related(
                Prefetch(
                    "users",
                    queryset=User.objects.all().only(*PARTIAL_USER_SERIALIZER_MODEL_FIELDS),
                )
            )
        else:
            base_qs = base_qs.prefetch_related(
                Prefetch("users", queryset=User.objects.all().only("id"))
            )

        if self.serializer_class(context={"request": self.request})._should_include_children:
            base_qs = base_qs.prefetch_related("children")

        if self.serializer_class(context={"request": self.request})._should_include_parents:
            base_qs = base_qs.prefetch_related("parents")

        return base_qs

    @extend_schema(
        parameters=[
            OpenApiParameter("include_users", bool, default=True),
            OpenApiParameter("include_children", bool, default=False),
            OpenApiParameter("include_parents", bool, default=False),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter("include_users", bool, default=True),
            OpenApiParameter("include_children", bool, default=False),
            OpenApiParameter("include_parents", bool, default=False),
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
        permission_classes=[IsAuthenticated],
    )
    @validate(UserAccountSerializer)
    def add_user(self, request: Request, body: UserAccountSerializer, pk: str) -> Response:
        """Add user to group"""
        group: Group = self.get_object()
        user: User = (
            get_objects_for_user(request.user, "authentik_core.view_user")
            .filter(
                pk=body.validated_data.get("pk"),
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
    @validate(UserAccountSerializer)
    def remove_user(self, request: Request, body: UserAccountSerializer, pk: str) -> Response:
        """Remove user from group"""
        group: Group = self.get_object()
        user: User = (
            get_objects_for_user(request.user, "authentik_core.view_user")
            .filter(
                pk=body.validated_data.get("pk"),
            )
            .first()
        )
        if not user:
            raise Http404
        group.users.remove(user)
        return Response(status=204)
