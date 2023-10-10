"""common RBAC serializers"""
from django_filters.filters import CharFilter
from django_filters.filterset import FilterSet
from guardian.models import GroupObjectPermission
from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import GenericViewSet

from authentik.rbac.api.rbac import RoleObjectPermissionSerializer


class RolePermissionFilter(FilterSet):
    name = CharFilter("group__role__name", required=True)


class RolePermissionViewSet(ListModelMixin, GenericViewSet):
    """Get a role's assigned object permissions"""

    serializer_class = RoleObjectPermissionSerializer
    ordering = ["group__role__name"]
    # The filtering is done in the filterset,
    # which has a required filter that does the heavy lifting
    queryset = GroupObjectPermission.objects.all()
    filterset_class = RolePermissionFilter
