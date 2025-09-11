"""SCIM Provider API Views"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.lib.sync.outgoing.api import OutgoingSyncProviderStatusMixin
from authentik.providers.scim.models import SCIMProvider
from authentik.providers.scim.tasks import scim_sync, scim_sync_objects


class SCIMProviderSerializer(ProviderSerializer):
    """SCIMProvider Serializer"""

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
            "compatibility_mode",
            "exclude_users_service_account",
            "filter_group",
            "dry_run",
        ]
        extra_kwargs = {}


class SCIMProviderViewSet(OutgoingSyncProviderStatusMixin, UsedByMixin, ModelViewSet):
    """SCIMProvider Viewset"""

    queryset = SCIMProvider.objects.all()
    serializer_class = SCIMProviderSerializer
    filterset_fields = ["name", "exclude_users_service_account", "url", "filter_group"]
    search_fields = ["name", "url"]
    ordering = ["name", "url"]
    sync_task = scim_sync
    sync_objects_task = scim_sync_objects
