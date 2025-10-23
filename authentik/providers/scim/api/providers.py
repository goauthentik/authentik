"""SCIM Provider API Views"""

from authentik.core.api.providers import ProviderSerializer
from authentik.lib.sync.outgoing.api import OutgoingSyncProviderViewSet
from authentik.lib.utils.reflection import ConditionalInheritance
from authentik.providers.scim.models import SCIMProvider
from authentik.providers.scim.tasks import scim_sync, scim_sync_objects


class SCIMProviderSerializer(
    ConditionalInheritance("authentik.enterprise.providers.scim.api.SCIMProviderSerializerMixin"),
    ProviderSerializer,
):
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
            "auth_mode",
            "auth_oauth",
            "auth_oauth_params",
            "compatibility_mode",
            "exclude_users_service_account",
            "filter_group",
            "sync_page_size",
            "sync_page_timeout",
            "dry_run",
        ]
        extra_kwargs = {}


class SCIMProviderViewSet(OutgoingSyncProviderViewSet):
    """SCIMProvider Viewset"""

    queryset = SCIMProvider.objects.all()
    serializer_class = SCIMProviderSerializer
    filterset_fields = OutgoingSyncProviderViewSet.filterset_fields + [
        "url",
    ]
    search_fields = OutgoingSyncProviderViewSet.search_fields + [
        "url",
    ]
    sync_task = scim_sync
    sync_objects_task = scim_sync_objects
