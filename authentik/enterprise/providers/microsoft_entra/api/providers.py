"""Microsoft Provider API Views"""

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.providers.microsoft_entra.models import (
    MicrosoftEntraProvider,
    MicrosoftEntraProviderSync,
)
from authentik.enterprise.providers.microsoft_entra.tasks import (
    microsoft_entra_sync,
    microsoft_entra_sync_objects,
)
from authentik.lib.sync.outgoing.api import OutgoingSyncProviderMixin, ProviderSyncSerializer
from authentik.rbac.filters import ObjectFilter


class MicrosoftEntraProviderSyncSerializer(ProviderSyncSerializer):
    class Meta:
        model = MicrosoftEntraProviderSync
        fields = ProviderSyncSerializer.Meta.fields


class MicrosoftEntraProviderSerializer(EnterpriseRequiredMixin, ProviderSerializer):
    """MicrosoftEntraProvider Serializer"""

    last_sync = MicrosoftEntraProviderSyncSerializer(read_only=True)

    class Meta:
        model = MicrosoftEntraProvider
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
            "client_id",
            "client_secret",
            "tenant_id",
            "exclude_users_service_account",
            "filter_group",
            "user_delete_action",
            "group_delete_action",
            "sync_page_size",
            "discovery_enabled",
            "sync_page_timeout",
            "dry_run",
            "last_sync",
        ]
        extra_kwargs = {}


class MicrosoftEntraProviderViewSet(OutgoingSyncProviderMixin, UsedByMixin, ModelViewSet):
    """MicrosoftEntraProvider Viewset"""

    queryset = MicrosoftEntraProvider.objects.prefetch_related(
        "microsoftentraprovidersync_set"
    ).all()
    serializer_class = MicrosoftEntraProviderSerializer
    filterset_fields = [
        "name",
        "exclude_users_service_account",
        "filter_group",
    ]
    search_fields = ["name"]
    ordering = ["name"]
    sync_task = microsoft_entra_sync
    sync_objects_task = microsoft_entra_sync_objects
    sync_serializer = MicrosoftEntraProviderSyncSerializer

    @extend_schema(responses={200: MicrosoftEntraProviderSyncSerializer(many=True)})
    @action(methods=["GET"], detail=True, filter_backends=[ObjectFilter])
    def syncs(self, request: Request, pk: int) -> Response:
        return self._syncs()
