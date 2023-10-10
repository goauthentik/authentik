"""common RBAC serializers"""
from django_filters.filters import CharFilter
from django_filters.filterset import FilterSet
from guardian.models import UserObjectPermission
from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import GenericViewSet

from authentik.rbac.api.rbac import UserObjectPermissionSerializer


class UserPermissionFilter(FilterSet):

    username = CharFilter("user__username", required=True)



class UserPermissionViewSet(ListModelMixin, GenericViewSet):
    """Get a users's assigned object permissions"""

    serializer_class = UserObjectPermissionSerializer
    ordering = ["user__username"]
    # The filtering is done in the filterset,
    # which has a required filter that does the heavy lifting
    queryset = UserObjectPermission.objects.all()
    filterset_class = UserPermissionFilter
