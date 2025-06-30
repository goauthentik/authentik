"""RAC Provider API Views"""

from rest_framework.fields import CharField, ListField
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.providers.rac.models import RACProvider


class RACProviderSerializer(ProviderSerializer):
    """RACProvider Serializer"""

    outpost_set = ListField(child=CharField(), read_only=True, source="outpost_set.all")

    class Meta:
        model = RACProvider
        fields = [
            "pk",
            "name",
            "authentication_flow",
            "authorization_flow",
            "property_mappings",
            "component",
            "assigned_application_slug",
            "assigned_application_name",
            "assigned_backchannel_application_slug",
            "assigned_backchannel_application_name",
            "verbose_name",
            "verbose_name_plural",
            "meta_model_name",
            "settings",
            "outpost_set",
            "connection_expiry",
            "delete_token_on_disconnect",
        ]
        extra_kwargs = {
            "authorization_flow": {"required": True, "allow_null": False},
        }


class RACProviderViewSet(UsedByMixin, ModelViewSet):
    """RACProvider Viewset"""

    queryset = RACProvider.objects.all()
    serializer_class = RACProviderSerializer
    filterset_fields = {
        "application": ["isnull"],
        "name": ["iexact"],
    }
    search_fields = ["name"]
    ordering = ["name"]
