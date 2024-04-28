"""Google Provider API Views"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.providers.google_workspace.models import GoogleWorkspaceProvider
from authentik.lib.sync.outgoing.api import OutgoingSyncProviderStatusMixin


class GoogleProviderSerializer(EnterpriseRequiredMixin, ProviderSerializer):
    """GoogleProvider Serializer"""

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
        ]
        extra_kwargs = {}


class GoogleProviderViewSet(OutgoingSyncProviderStatusMixin, UsedByMixin, ModelViewSet):
    """GoogleProvider Viewset"""

    queryset = GoogleWorkspaceProvider.objects.all()
    serializer_class = GoogleProviderSerializer
    filterset_fields = [
        "name",
        "exclude_users_service_account",
        "delegated_subject",
        "filter_group",
    ]
    search_fields = ["name"]
    ordering = ["name"]
