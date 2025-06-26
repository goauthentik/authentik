"""Google Provider API Views"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.providers.google_workspace.models import GoogleWorkspaceProvider
from authentik.enterprise.providers.google_workspace.tasks import (
    google_workspace_sync,
    google_workspace_sync_objects,
)
from authentik.lib.sync.outgoing.api import OutgoingSyncProviderStatusMixin


class GoogleWorkspaceProviderSerializer(EnterpriseRequiredMixin, ProviderSerializer):
    """GoogleWorkspaceProvider Serializer"""

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
            "dry_run",
        ]
        extra_kwargs = {}


class GoogleWorkspaceProviderViewSet(OutgoingSyncProviderStatusMixin, UsedByMixin, ModelViewSet):
    """GoogleWorkspaceProvider Viewset"""

    queryset = GoogleWorkspaceProvider.objects.all()
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
