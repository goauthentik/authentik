"""SCIM Provider API Views"""

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.fields import SerializerMethodField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.lib.sync.outgoing.api import OutgoingSyncProviderMixin, ProviderSyncSerializer
from authentik.lib.utils.reflection import ConditionalInheritance
from authentik.providers.scim.models import SCIMProvider, SCIMProviderSync
from authentik.providers.scim.tasks import scim_sync, scim_sync_objects
from authentik.rbac.filters import ObjectFilter


class SCIMProviderSyncSerializer(ProviderSyncSerializer):
    class Meta:
        model = SCIMProviderSync
        fields = ProviderSyncSerializer.Meta.fields


class SCIMProviderSerializer(
    ConditionalInheritance("authentik.enterprise.providers.scim.api.SCIMProviderSerializerMixin"),
    ProviderSerializer,
):
    """SCIMProvider Serializer"""

    auth_oauth_token_last_updated = SerializerMethodField()
    auth_oauth_token_expires = SerializerMethodField()
    auth_oauth_url_callback = SerializerMethodField()
    auth_oauth_url_start = SerializerMethodField()

    last_sync = SCIMProviderSyncSerializer(read_only=True)

    class Meta:
        model = SCIMProvider
        fields = [
            "pk",
            "name",
            "property_mappings",
            "property_mappings_group",
            "component",
            "assigned_backchannel_application_slug",
            "assigned_backchannel_application_name",
            "verbose_name",
            "verbose_name_plural",
            "meta_model_name",
            "url",
            "verify_certificates",
            "token",
            "auth_mode",
            "auth_oauth",
            "auth_oauth_params",
            "auth_oauth_token_last_updated",
            "auth_oauth_token_expires",
            "auth_oauth_url_callback",
            "auth_oauth_url_start",
            "compatibility_mode",
            "service_provider_config_cache_timeout",
            "exclude_users_service_account",
            "sync_page_size",
            "sync_page_timeout",
            "discovery_enabled",
            "group_filters",
            "dry_run",
            "last_sync",
        ]
        extra_kwargs = {}


class SCIMProviderViewSet(OutgoingSyncProviderMixin, UsedByMixin, ModelViewSet):
    """SCIMProvider Viewset"""

    queryset = SCIMProvider.objects.prefetch_related("scimprovidersync_set").all()
    serializer_class = SCIMProviderSerializer
    filterset_fields = ["name", "exclude_users_service_account", "url", "group_filters"]
    search_fields = ["name", "url"]
    ordering = ["name", "url"]
    sync_task = scim_sync
    sync_objects_task = scim_sync_objects
    sync_serializer = SCIMProviderSyncSerializer

    @extend_schema(responses={200: SCIMProviderSyncSerializer(many=True)})
    @action(methods=["GET"], detail=True, filter_backends=[ObjectFilter])
    def syncs(self, request: Request, pk: int) -> Response:
        return self._syncs()
