"""Source API Views"""
from datetime import datetime
from time import time

from django.core.cache import cache
from django.db.models.base import Model
from drf_yasg2.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.fields import DateTimeField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.sources import SourceSerializer
from authentik.core.api.utils import MetaNameSerializer
from authentik.sources.ldap.models import LDAPPropertyMapping, LDAPSource


class LDAPSourceSerializer(SourceSerializer):
    """LDAP Source Serializer"""

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


class LDAPSourceSyncStatusSerializer(Serializer):
    """LDAP Sync status"""

    last_sync = DateTimeField(read_only=True)

    def create(self, validated_data: dict) -> Model:
        raise NotImplementedError

    def update(self, instance: Model, validated_data: dict) -> Model:
        raise NotImplementedError


class LDAPSourceViewSet(ModelViewSet):
    """LDAP Source Viewset"""

    queryset = LDAPSource.objects.all()
    serializer_class = LDAPSourceSerializer
    lookup_field = "slug"

    @swagger_auto_schema(responses={200: LDAPSourceSyncStatusSerializer(many=False)})
    @action(methods=["GET"], detail=True)
    # pylint: disable=unused-argument
    def sync_status(self, request: Request, slug: str) -> Response:
        """Get source's sync status"""
        source = self.get_object()
        last_sync = cache.get(source.state_cache_prefix("last_sync"), time())
        return Response(
            LDAPSourceSyncStatusSerializer(
                {"last_sync": datetime.fromtimestamp(last_sync)}
            ).data
        )


class LDAPPropertyMappingSerializer(ModelSerializer, MetaNameSerializer):
    """LDAP PropertyMapping Serializer"""

    class Meta:
        model = LDAPPropertyMapping
        fields = [
            "pk",
            "name",
            "expression",
            "object_field",
            "verbose_name",
            "verbose_name_plural",
        ]


class LDAPPropertyMappingViewSet(ModelViewSet):
    """LDAP PropertyMapping Viewset"""

    queryset = LDAPPropertyMapping.objects.all()
    serializer_class = LDAPPropertyMappingSerializer
