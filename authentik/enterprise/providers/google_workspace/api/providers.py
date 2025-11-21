"""Google Provider API Views"""

from authentik.core.api.providers import ProviderSerializer
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.providers.google_workspace.models import GoogleWorkspaceProvider
from authentik.enterprise.providers.google_workspace.tasks import (
    google_workspace_sync,
    google_workspace_sync_objects,
)
from authentik.lib.sync.outgoing.api import OutgoingSyncProviderViewSet


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
            "sync_page_size",
            "sync_page_timeout",
            "dry_run",
        ]
        extra_kwargs = {}


class GoogleWorkspaceProviderViewSet(OutgoingSyncProviderViewSet):
    """GoogleWorkspaceProvider Viewset"""

    queryset = GoogleWorkspaceProvider.objects.all()
    serializer_class = GoogleWorkspaceProviderSerializer
    filterset_fields = OutgoingSyncProviderViewSet.filterset_fields + [
        "delegated_subject",
    ]
    search_fields = OutgoingSyncProviderViewSet.search_fields + [
        "delegated_subject",
    ]
    sync_task = google_workspace_sync
    sync_objects_task = google_workspace_sync_objects
