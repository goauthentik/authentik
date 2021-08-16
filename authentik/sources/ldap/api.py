"""Source API Views"""
from typing import Any

from django.http.response import Http404
from django.utils.text import slugify
from django_filters.filters import AllValuesMultipleFilter
from django_filters.filterset import FilterSet
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentik.admin.api.tasks import TaskSerializer
from authentik.core.api.propertymappings import PropertyMappingSerializer
from authentik.core.api.sources import SourceSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.events.monitored_tasks import TaskInfo
from authentik.sources.ldap.models import LDAPPropertyMapping, LDAPSource


class LDAPSourceSerializer(SourceSerializer):
    """LDAP Source Serializer"""

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Check that only a single source has password_sync on"""
        sync_users_password = attrs.get("sync_users_password", True)
        if sync_users_password:
            if LDAPSource.objects.filter(sync_users_password=True).exists():
                raise ValidationError(
                    "Only a single LDAP Source with password synchronization is allowed"
                )
        return super().validate(attrs)

    class Meta:
        model = LDAPSource
        fields = SourceSerializer.Meta.fields + [
            "server_uri",
            "bind_cn",
            "bind_password",
            "start_tls",
            "base_dn",
            "additional_user_dn",
            "additional_group_dn",
            "user_object_filter",
            "group_object_filter",
            "group_membership_field",
            "object_uniqueness_field",
            "sync_users",
            "sync_users_password",
            "sync_groups",
            "sync_parent_group",
            "property_mappings",
            "property_mappings_group",
        ]
        extra_kwargs = {"bind_password": {"write_only": True}}


class LDAPSourceViewSet(UsedByMixin, ModelViewSet):
    """LDAP Source Viewset"""

    queryset = LDAPSource.objects.all()
    serializer_class = LDAPSourceSerializer
    lookup_field = "slug"
    filterset_fields = [
        "name",
        "slug",
        "enabled",
        "authentication_flow",
        "enrollment_flow",
        "policy_engine_mode",
        "server_uri",
        "bind_cn",
        "start_tls",
        "base_dn",
        "additional_user_dn",
        "additional_group_dn",
        "user_object_filter",
        "group_object_filter",
        "group_membership_field",
        "object_uniqueness_field",
        "sync_users",
        "sync_users_password",
        "sync_groups",
        "sync_parent_group",
        "property_mappings",
        "property_mappings_group",
    ]
    ordering = ["name"]

    @extend_schema(
        responses={
            200: TaskSerializer(many=False),
            404: OpenApiResponse(description="Task not found"),
        }
    )
    @action(methods=["GET"], detail=True)
    # pylint: disable=unused-argument
    def sync_status(self, request: Request, slug: str) -> Response:
        """Get source's sync status"""
        source = self.get_object()
        task = TaskInfo.by_name(f"ldap_sync_{slugify(source.name)}")
        if not task:
            raise Http404
        return Response(TaskSerializer(task, many=False).data)


class LDAPPropertyMappingSerializer(PropertyMappingSerializer):
    """LDAP PropertyMapping Serializer"""

    class Meta:
        model = LDAPPropertyMapping
        fields = PropertyMappingSerializer.Meta.fields + [
            "object_field",
        ]


class LDAPPropertyMappingFilter(FilterSet):
    """Filter for LDAPPropertyMapping"""

    managed = AllValuesMultipleFilter(field_name="managed")

    class Meta:
        model = LDAPPropertyMapping
        fields = "__all__"


class LDAPPropertyMappingViewSet(UsedByMixin, ModelViewSet):
    """LDAP PropertyMapping Viewset"""

    queryset = LDAPPropertyMapping.objects.all()
    serializer_class = LDAPPropertyMappingSerializer
    filterset_class = LDAPPropertyMappingFilter
    ordering = ["name"]
