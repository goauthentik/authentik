"""common RBAC serializers"""
from django.apps import apps
from django.db.models import Q, QuerySet
from django.db.transaction import atomic
from django_filters.filters import CharFilter, ChoiceFilter
from django_filters.filterset import FilterSet
from drf_spectacular.utils import OpenApiResponse, extend_schema
from guardian.shortcuts import assign_perm
from rest_framework.decorators import action
from rest_framework.fields import CharField
from rest_framework.mixins import ListModelMixin
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from authentik.core.api.rbac import PermissionAssignSerializer, RoleObjectPermissionSerializer
from authentik.core.api.utils import PassiveSerializer
from authentik.core.models import Role
from authentik.policies.event_matcher.models import model_choices


class RoleAssignedObjectPermissionSerializer(PassiveSerializer):
    name = CharField(source="group.name", read_only=True)
    permissions = RoleObjectPermissionSerializer(
        many=True, source="group.groupobjectpermission_set"
    )

    class Meta:
        model = Role
        fields = ["name", "permissions"]


class AssignedPermissionFilter(FilterSet):
    model = ChoiceFilter(choices=model_choices(), method="filter_model", required=True)
    object_pk = CharFilter(method="filter_object_pk")

    def filter_model(self, queryset: QuerySet, name, value: str) -> QuerySet:
        app, _, model = value.partition(".")
        return queryset.filter(
            Q(
                group__permissions__content_type__app_label=app,
                group__permissions__content_type__model=model,
            )
            | Q(
                group__groupobjectpermission__permission__content_type__app_label=app,
                group__groupobjectpermission__permission__content_type__model=model,
            )
        )

    def filter_object_pk(self, queryset: QuerySet, name, value: str) -> QuerySet:
        return queryset.filter(Q(group__groupobjectpermission__object_pk=value))


class RoleAssignedPermissionViewSet(ListModelMixin, GenericViewSet):
    """Get assigned object permissions for a single object"""

    serializer_class = RoleAssignedObjectPermissionSerializer
    # The filtering is done in the filterset,
    # which has a required filter that does the heavy lifting
    queryset = Role.objects.all()
    filterset_class = AssignedPermissionFilter

    @extend_schema(
        request=PermissionAssignSerializer(),
        responses={
            204: OpenApiResponse(description="Successfully assigned"),
        },
    )
    @action(methods=["POST"], detail=True, pagination_class=None, filter_backends=[])
    def assign(self, request: Request, *args, **kwargs) -> Response:
        """Assign permission(s) to role"""
        role: Role = self.get_object()
        data = PermissionAssignSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        model = apps.get_model(data.validated_data["model"])
        model_instance = model.objects.filter(pk=data.validated_data["object_pk"])
        with atomic():
            for perm in data.validated_data["permissions"]:
                assign_perm(perm, role.group, model_instance)
        return Response(status=204)
