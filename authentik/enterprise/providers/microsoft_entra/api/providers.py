"""Microsoft Provider API Views"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.providers.microsoft_entra.models import MicrosoftEntraProvider
from authentik.enterprise.providers.microsoft_entra.tasks import microsoft_entra_sync
from authentik.lib.sync.outgoing.api import OutgoingSyncProviderStatusMixin


class MicrosoftProviderSerializer(EnterpriseRequiredMixin, ProviderSerializer):
    """MicrosoftProvider Serializer"""

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
        ]
        extra_kwargs = {}


class MicrosoftProviderViewSet(OutgoingSyncProviderStatusMixin, UsedByMixin, ModelViewSet):
    """MicrosoftProvider Viewset"""

    queryset = MicrosoftEntraProvider.objects.all()
    serializer_class = MicrosoftProviderSerializer
    filterset_fields = [
        "name",
        "exclude_users_service_account",
        "filter_group",
    ]
    search_fields = ["name"]
    ordering = ["name"]
    sync_single_task = microsoft_entra_sync
