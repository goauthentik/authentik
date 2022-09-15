"""Groups API Viewset"""
from json import loads

from django.db.models.query import QuerySet
from django_filters.filters import CharFilter, ModelMultipleChoiceFilter
from django_filters.filterset import FilterSet
from rest_framework.fields import CharField, IntegerField, JSONField
from rest_framework.serializers import ListSerializer, ModelSerializer, ValidationError
from rest_framework.viewsets import ModelViewSet
from rest_framework_guardian.filters import ObjectPermissionsFilter

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import is_dict
from authentik.core.models import Group, User


class GroupMemberSerializer(ModelSerializer):
    """Stripped down user serializer to show relevant users for groups"""

    avatar = CharField(read_only=True)
    attributes = JSONField(validators=[is_dict], required=False)
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
            "avatar",
            "attributes",
            "uid",
        ]


class GroupSerializer(ModelSerializer):
    """Group Serializer"""

    attributes = JSONField(validators=[is_dict], required=False)
    users_obj = ListSerializer(
        child=GroupMemberSerializer(), read_only=True, source="users", required=False
    )
    parent_name = CharField(source="parent.name", read_only=True)

    num_pk = IntegerField(read_only=True)

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
            "attributes",
            "users_obj",
        ]
        extra_kwargs = {
            "users": {
                "default": list,
            }
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

    # pylint: disable=unused-argument
    def filter_attributes(self, queryset, name, value):
        """Filter attributes by query args"""
        try:
            value = loads(value)
        except ValueError:
            raise ValidationError(detail="filter: failed to parse JSON")
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

    queryset = Group.objects.all().select_related("parent").prefetch_related("users")
    serializer_class = GroupSerializer
    search_fields = ["name", "is_superuser"]
    filterset_class = GroupFilter
    ordering = ["name"]

    def _filter_queryset_for_list(self, queryset: QuerySet) -> QuerySet:
        """Custom filter_queryset method which ignores guardian, but still supports sorting"""
        for backend in list(self.filter_backends):
            if backend == ObjectPermissionsFilter:
                continue
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    def filter_queryset(self, queryset):
        if self.request.user.has_perm("authentik_core.view_group"):
            return self._filter_queryset_for_list(queryset)
        return super().filter_queryset(queryset)
