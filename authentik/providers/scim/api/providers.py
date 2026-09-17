"""SCIM Provider API Views"""

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.fields import SerializerMethodField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.lib.sync.outgoing.api import OutgoingSyncProviderStatusMixin
from authentik.lib.utils.reflection import ConditionalInheritance
from authentik.providers.scim.api.resource_types import (
    SCIMResourceTypeDiscoveryQuerySerializer,
    SCIMResourceTypeDiscoverySerializer,
)
from authentik.providers.scim.clients.resource_types import SCIMResourceTypesClient
from authentik.providers.scim.models import SCIMProvider
from authentik.providers.scim.tasks import scim_sync, scim_sync_objects
from authentik.rbac.filters import ObjectFilter


class SCIMProviderSerializer(
    ConditionalInheritance("authentik.enterprise.providers.scim.api.SCIMProviderSerializerMixin"),
    ProviderSerializer,
):
    """SCIMProvider Serializer"""

    auth_oauth_token_last_updated = SerializerMethodField()
    auth_oauth_token_expires = SerializerMethodField()
    auth_oauth_url_callback = SerializerMethodField()
    auth_oauth_url_start = SerializerMethodField()

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
        ]
        extra_kwargs = {"token": {"write_only": True}}


class SCIMProviderViewSet(OutgoingSyncProviderStatusMixin, UsedByMixin, ModelViewSet):
    """SCIMProvider Viewset"""

    queryset = SCIMProvider.objects.all()
    serializer_class = SCIMProviderSerializer
    filterset_fields = ["name", "exclude_users_service_account", "url", "group_filters"]
    search_fields = ["name", "url"]
    ordering = ["name", "url"]
    sync_task = scim_sync
    sync_objects_task = scim_sync_objects

    @extend_schema(
        parameters=[SCIMResourceTypeDiscoveryQuerySerializer],
        responses={200: SCIMResourceTypeDiscoverySerializer()},
    )
    @action(methods=["GET"], detail=True, pagination_class=None, filter_backends=[ObjectFilter])
    def resource_types(self, request: Request, pk: int) -> Response:
        """Inspect the destination's advertised resource types without changing sync behavior."""
        provider = self.get_object()
        query = SCIMResourceTypeDiscoveryQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        result = SCIMResourceTypesClient(provider).get_resource_types(
            force_refresh=query.validated_data["refresh"]
        )
        return Response(SCIMResourceTypeDiscoverySerializer(result).data)
