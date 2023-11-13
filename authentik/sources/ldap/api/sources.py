"""Source API Views"""
from typing import Any, Optional

from django.core.cache import cache
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.fields import BooleanField, DictField, ListField, SerializerMethodField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentik.admin.api.tasks import TaskSerializer
from authentik.core.api.sources import SourceSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import PassiveSerializer
from authentik.crypto.models import CertificateKeyPair
from authentik.events.monitored_tasks import TaskInfo
from authentik.sources.ldap.models import LDAPSource
from authentik.sources.ldap.tasks import CACHE_KEY_STATUS, SYNC_CLASSES, ldap_sync_single


class LDAPSourceSerializer(SourceSerializer):
    """LDAP Source Serializer"""

    connectivity = SerializerMethodField()
    client_certificate = PrimaryKeyRelatedField(
        allow_null=True,
        help_text="Client certificate to authenticate against the LDAP Server's Certificate.",
        queryset=CertificateKeyPair.objects.exclude(
            key_data__exact="",
        ),
        required=False,
    )

    def get_connectivity(self, source: LDAPSource) -> Optional[dict[str, dict[str, str]]]:
        """Get cached source connectivity"""
        return cache.get(CACHE_KEY_STATUS + source.slug, None)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Check that only a single source has password_sync on"""
        sync_users_password = attrs.get("sync_users_password", True)
        if sync_users_password:
            sources = LDAPSource.objects.filter(sync_users_password=True)
            if self.instance:
                sources = sources.exclude(pk=self.instance.pk)
            if sources.exists():
                raise ValidationError(
                    {
                        "sync_users_password": (
                            "Only a single LDAP Source with password synchronization is allowed"
                        )
                    }
                )
        return super().validate(attrs)

    def create(self, validated_data) -> LDAPSource:
        # Create both creates the actual model and assigns m2m fields
        instance: LDAPSource = super().create(validated_data)
        if not instance.enabled:
            return instance
        # Don't sync sources when they don't have any property mappings. This will only happen if:
        # - the user forgets to set them or
        # - the source is newly created, this is the first save event
        #   and the mappings are created with an m2m event
        if not instance.property_mappings.exists() or not instance.property_mappings_group.exists():
            return instance
        ldap_sync_single.delay(instance.pk)
        return instance

    class Meta:
        model = LDAPSource
        fields = SourceSerializer.Meta.fields + [
            "server_uri",
            "peer_certificate",
            "client_certificate",
            "bind_cn",
            "bind_password",
            "start_tls",
            "sni",
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
            "connectivity",
        ]
        extra_kwargs = {"bind_password": {"write_only": True}}


class LDAPSyncStatusSerializer(PassiveSerializer):
    """LDAP Source sync status"""

    is_running = BooleanField(read_only=True)
    tasks = TaskSerializer(many=True, read_only=True)


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
        "client_certificate",
        "start_tls",
        "sni",
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
        request=None,
        responses={
            200: LDAPSyncStatusSerializer(),
        },
    )
    @action(methods=["GET", "POST"], detail=True, pagination_class=None, filter_backends=[])
    def sync(self, request: Request, slug: str) -> Response:
        """Get source's sync status or start source sync"""
        source = self.get_object()
        if request.method == "POST":
            # We're not waiting for the sync to finish here as it could take multiple hours
            ldap_sync_single.delay(source.pk)
        tasks = TaskInfo.by_name(f"ldap_sync:{source.slug}:*") or []
        status = {
            "tasks": tasks,
            "is_running": source.sync_lock.locked(),
        }
        return Response(LDAPSyncStatusSerializer(status).data)

    @extend_schema(
        responses={
            200: inline_serializer(
                "LDAPDebugSerializer",
                fields={
                    "user": ListField(child=DictField(), read_only=True),
                    "group": ListField(child=DictField(), read_only=True),
                    "membership": ListField(child=DictField(), read_only=True),
                },
            ),
        }
    )
    @action(methods=["GET"], detail=True, pagination_class=None, filter_backends=[])
    def debug(self, request: Request, slug: str) -> Response:
        """Get raw LDAP data to debug"""
        source = self.get_object()
        all_objects = {}
        for sync_class in SYNC_CLASSES:
            class_name = sync_class.name()
            all_objects.setdefault(class_name, [])
            for obj in sync_class(source).get_objects(size_limit=10):
                obj: dict
                obj.pop("raw_attributes", None)
                obj.pop("raw_dn", None)
                all_objects[class_name].append(obj)
        return Response(data=all_objects)
