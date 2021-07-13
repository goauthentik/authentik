"""Groups API Viewset"""
from django.db.models.query import QuerySet
from rest_framework.fields import BooleanField, CharField, JSONField
from rest_framework.serializers import ListSerializer, ModelSerializer
from rest_framework.viewsets import ModelViewSet
from rest_framework_guardian.filters import ObjectPermissionsFilter

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import is_dict
from authentik.core.models import Group, User


class GroupMemberSerializer(ModelSerializer):
    """Stripped down user serializer to show relevant users for groups"""

    is_superuser = BooleanField(read_only=True)
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
            "is_superuser",
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

    class Meta:

        model = Group
        fields = [
            "pk",
            "name",
            "is_superuser",
            "parent",
            "users",
            "attributes",
            "users_obj",
        ]


class GroupViewSet(UsedByMixin, ModelViewSet):
    """Group Viewset"""

    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    search_fields = ["name", "is_superuser"]
    filterset_fields = ["name", "is_superuser"]
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
