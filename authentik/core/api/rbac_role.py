"""common RBAC serializers"""
from django.contrib.auth.models import Group
from django.db.models import Q, QuerySet
from django_filters.filters import CharFilter, ChoiceFilter
from django_filters.filterset import FilterSet
from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import GenericViewSet

from authentik.core.api.rbac import GroupObjectPermissionSerializer
from authentik.core.api.users import UserGroupSerializer
from authentik.policies.event_matcher.models import model_choices


class RoleAssignedObjectPermissionSerializer(UserGroupSerializer):
    permissions = GroupObjectPermissionSerializer(many=True, source="groupobjectpermission_set")

    class Meta:
        model = UserGroupSerializer.Meta.model
        fields = UserGroupSerializer.Meta.fields + ["permissions"]


class AssignedPermissionFilter(FilterSet):
    model = ChoiceFilter(choices=model_choices(), method="filter_model", required=True)
    object_pk = CharFilter(method="filter_object_pk")

    def filter_model(self, queryset: QuerySet, name, value: str) -> QuerySet:
        app, _, model = value.partition(".")
        return queryset.filter(
            Q(
                permissions__content_type__app_label=app,
                permissions__content_type__model=model,
            )
            | Q(
                groupobjectpermission__permission__content_type__app_label=app,
                groupobjectpermission__permission__content_type__model=model,
            )
        )

    def filter_object_pk(self, queryset: QuerySet, name, value: str) -> QuerySet:
        return queryset.filter(Q(groupobjectpermission__object_pk=value))


class RoleAssignedPermissionViewSet(ListModelMixin, GenericViewSet):
    """Get assigned object permissions for a single object"""

    serializer_class = RoleAssignedObjectPermissionSerializer
    # The filtering is done in the filterset,
    # which has a required filter that does the heavy lifting
    queryset = Group.objects.all()
    filterset_class = AssignedPermissionFilter
