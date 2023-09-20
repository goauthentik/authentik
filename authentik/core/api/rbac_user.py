"""common RBAC serializers"""
from django.db.models import Q, QuerySet
from django_filters.filters import CharFilter, ChoiceFilter
from django_filters.filterset import FilterSet
from rest_framework.fields import BooleanField
from rest_framework.mixins import ListModelMixin, CreateModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework.request import Request
from rest_framework.response import Response
from authentik.core.api.groups import GroupMemberSerializer
from authentik.core.api.rbac import UserObjectPermissionSerializer
from authentik.core.api.utils import PassiveSerializer
from authentik.core.models import User
from authentik.policies.event_matcher.models import model_choices
from rest_framework.decorators import action
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from drf_spectacular.types import OpenApiTypes
from rest_framework.fields import ChoiceField, ListField, CharField
from guardian.shortcuts import assign_perm
from django.db.transaction import atomic
from django.apps import apps
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


class UserAssignSerializer(PassiveSerializer):

    permissions = ListField(child=CharField())
    model = ChoiceField(choices=model_choices())
    object_pk = CharField()

class UserAssignedPermissionViewSet(CreateModelMixin, ListModelMixin, GenericViewSet):
    """Get assigned object permissions for a single object"""

    serializer_class = UserAssignedObjectPermissionSerializer
    # The filtering is done in the filterset,
    # which has a required filter that does the heavy lifting
    queryset = User.objects.all()
    filterset_class = AssignedPermissionFilter

    @extend_schema(
        request=UserAssignSerializer()
    )
    @action(methods=["POST"], detail=True)
    def assign(self, request: Request, *args, **kwargs) -> Response:
        """Assign permission(s) to user"""
        user = self.get_object()
        data = UserAssignSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        model = apps.get_model(data.validated_data["model"])
        model_instance = model.objects.filter(pk=data.validated_data["object_pk"])
        with atomic():
            for perm in data.validated_data["permissions"]:
                assign_perm(perm, user, model_instance)
        return Response(status=200)
