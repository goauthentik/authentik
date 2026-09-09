"""Google Provider API Views"""

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.providers.google_workspace.models import (
    GoogleWorkspaceProvider,
    GoogleWorkspaceProviderSync,
)
from authentik.enterprise.providers.google_workspace.tasks import (
    google_workspace_sync,
    google_workspace_sync_objects,
)
from authentik.lib.sync.outgoing.api import OutgoingSyncProviderMixin, ProviderSyncSerializer
from authentik.rbac.filters import ObjectFilter


class GoogleWorkspaceProviderSyncSerializer(ProviderSyncSerializer):
    class Meta:
        model = GoogleWorkspaceProviderSync
        fields = ProviderSyncSerializer.Meta.fields


class GoogleWorkspaceProviderSerializer(EnterpriseRequiredMixin, ProviderSerializer):
    """GoogleWorkspaceProvider Serializer"""

    last_sync = GoogleWorkspaceProviderSyncSerializer(read_only=True)

    class Meta:
        model = GoogleWorkspaceProvider
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
            "delegated_subject",
            "credentials",
            "scopes",
            "exclude_users_service_account",
            "filter_group",
            "user_delete_action",
            "group_delete_action",
            "default_group_email_domain",
            "sync_page_size",
            "sync_page_timeout",
            "dry_run",
            "discovery_enabled",
            "last_sync",
        ]
        extra_kwargs = {}


class GoogleWorkspaceProviderViewSet(OutgoingSyncProviderMixin, UsedByMixin, ModelViewSet):
    """GoogleWorkspaceProvider Viewset"""

    queryset = GoogleWorkspaceProvider.objects.prefetch_related(
        "googleworkspaceprovidersync_set"
    ).all()
    serializer_class = GoogleWorkspaceProviderSerializer
    filterset_fields = [
        "name",
        "exclude_users_service_account",
        "delegated_subject",
        "filter_group",
    ]
    search_fields = ["name"]
    ordering = ["name"]
    sync_task = google_workspace_sync
    sync_objects_task = google_workspace_sync_objects
    sync_serializer = GoogleWorkspaceProviderSyncSerializer

    @extend_schema(responses={200: GoogleWorkspaceProviderSyncSerializer(many=True)})
    @action(methods=["GET"], detail=True, filter_backends=[ObjectFilter])
    def syncs(self, request: Request, pk: int) -> Response:
        return self._syncs()
