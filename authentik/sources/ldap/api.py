"""Source API Views"""
from typing import Any

from django_filters.filters import AllValuesMultipleFilter
from django_filters.filterset import FilterSet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_field
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
from authentik.sources.ldap.sync.groups import GroupLDAPSynchronizer
from authentik.sources.ldap.sync.membership import MembershipLDAPSynchronizer
from authentik.sources.ldap.sync.users import UserLDAPSynchronizer


class LDAPSourceSerializer(SourceSerializer):
    """LDAP Source Serializer"""

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Check that only a single source has password_sync on"""
        sync_users_password = attrs.get("sync_users_password", True)
        if sync_users_password:
            sources = LDAPSource.objects.filter(sync_users_password=True)
            if self.instance:
                sources = sources.exclude(pk=self.instance.pk)
            if sources.exists():
                raise ValidationError(
                    "Only a single LDAP Source with password synchronization is allowed"
                )
        return super().validate(attrs)

    class Meta:
        model = LDAPSource
        fields = SourceSerializer.Meta.fields + [
            "server_uri",
            "peer_certificate",
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
        "server_uri",
        "bind_cn",
        "peer_certificate",
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
    search_fields = ["name", "slug"]
    ordering = ["name"]

    @extend_schema(
        responses={
            200: TaskSerializer(many=True),
        }
    )
    @action(methods=["GET"], detail=True, pagination_class=None, filter_backends=[])
    # pylint: disable=unused-argument
    def sync_status(self, request: Request, slug: str) -> Response:
        """Get source's sync status"""
        source = self.get_object()
        results = []
        for sync_class in [
            UserLDAPSynchronizer,
            GroupLDAPSynchronizer,
            MembershipLDAPSynchronizer,
        ]:
            sync_name = sync_class.__name__.replace("LDAPSynchronizer", "").lower()
            task = TaskInfo.by_name(f"ldap_sync_{source.slug}_{sync_name}")
            if task:
                results.append(task)
        return Response(TaskSerializer(results, many=True).data)


class LDAPPropertyMappingSerializer(PropertyMappingSerializer):
    """LDAP PropertyMapping Serializer"""

    class Meta:
        model = LDAPPropertyMapping
        fields = PropertyMappingSerializer.Meta.fields + [
            "object_field",
        ]


class LDAPPropertyMappingFilter(FilterSet):
    """Filter for LDAPPropertyMapping"""

    managed = extend_schema_field(OpenApiTypes.STR)(AllValuesMultipleFilter(field_name="managed"))

    class Meta:
        model = LDAPPropertyMapping
        fields = "__all__"


class LDAPPropertyMappingViewSet(UsedByMixin, ModelViewSet):
    """LDAP PropertyMapping Viewset"""

    queryset = LDAPPropertyMapping.objects.all()
    serializer_class = LDAPPropertyMappingSerializer
    filterset_class = LDAPPropertyMappingFilter
    search_fields = ["name"]
    ordering = ["name"]
