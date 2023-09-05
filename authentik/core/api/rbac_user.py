"""common RBAC serializers"""
from django.db.models import Q, QuerySet
from django_filters.filters import CharFilter, ChoiceFilter
from django_filters.filterset import FilterSet
from rest_framework.fields import BooleanField
from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import GenericViewSet

from authentik.core.api.groups import GroupMemberSerializer
from authentik.core.api.rbac import UserObjectPermissionSerializer
from authentik.core.models import User
from authentik.policies.event_matcher.models import model_choices


class UserAssignedObjectPermissionSerializer(GroupMemberSerializer):
    permissions = UserObjectPermissionSerializer(many=True, source="userobjectpermission_set")
    is_superuser = BooleanField()

    class Meta:
        model = GroupMemberSerializer.Meta.model
        fields = GroupMemberSerializer.Meta.fields + ["permissions", "is_superuser"]


class AssignedPermissionFilter(FilterSet):
    model = ChoiceFilter(choices=model_choices(), method="filter_model", required=True)
    object_pk = CharFilter(method="filter_object_pk")

    def filter_model(self, queryset: QuerySet, name, value: str) -> QuerySet:
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
        )

    def filter_object_pk(self, queryset: QuerySet, name, value: str) -> QuerySet:
        return queryset.filter(
            Q(userobjectpermission__object_pk=value) | Q(ak_groups__is_superuser=True),
        )


class UserAssignedPermissionViewSet(ListModelMixin, GenericViewSet):
    """Get assigned object permissions for a single object"""

    serializer_class = UserAssignedObjectPermissionSerializer
    # The filtering is done in the filterset,
    # which has a required filter that does the heavy lifting
    queryset = User.objects.all()
    filterset_class = AssignedPermissionFilter
