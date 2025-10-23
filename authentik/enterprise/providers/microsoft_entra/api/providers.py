"""Microsoft Provider API Views"""

from authentik.core.api.providers import ProviderSerializer
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.providers.microsoft_entra.models import MicrosoftEntraProvider
from authentik.enterprise.providers.microsoft_entra.tasks import (
    microsoft_entra_sync,
    microsoft_entra_sync_objects,
)
from authentik.lib.sync.outgoing.api import OutgoingSyncProviderViewSet


class MicrosoftEntraProviderSerializer(EnterpriseRequiredMixin, ProviderSerializer):
    """MicrosoftEntraProvider Serializer"""

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
            "sync_page_timeout",
            "dry_run",
        ]
        extra_kwargs = {}


class MicrosoftEntraProviderViewSet(OutgoingSyncProviderViewSet):
    """MicrosoftEntraProvider Viewset"""

    queryset = MicrosoftEntraProvider.objects.all()
    serializer_class = MicrosoftEntraProviderSerializer
    sync_task = microsoft_entra_sync
    sync_objects_task = microsoft_entra_sync_objects
