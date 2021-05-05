"""Groups API Viewset"""
from django.db.models.query import QuerySet
from rest_framework.fields import JSONField
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet
from rest_framework_guardian.filters import ObjectPermissionsFilter

from authentik.core.api.utils import is_dict
from authentik.core.models import Group


class GroupSerializer(ModelSerializer):
    """Group Serializer"""

    attributes = JSONField(validators=[is_dict], required=False)

    class Meta:

        model = Group
        fields = ["pk", "name", "is_superuser", "parent", "users", "attributes"]


class GroupViewSet(ModelViewSet):
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
