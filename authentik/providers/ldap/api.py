"""LDAPProvider API Views"""
from rest_framework.fields import CharField, ListField, SerializerMethodField
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.providers.ldap.models import LDAPProvider


class LDAPProviderSerializer(ProviderSerializer):
    """LDAPProvider Serializer"""

    outpost_set = ListField(child=CharField(), read_only=True, source="outpost_set.all")

    class Meta:
        model = LDAPProvider
        fields = ProviderSerializer.Meta.fields + [
            "base_dn",
            "search_group",
            "certificate",
            "tls_server_name",
            "uid_start_number",
            "gid_start_number",
            "outpost_set",
            "search_mode",
            "bind_mode",
        ]
        extra_kwargs = ProviderSerializer.Meta.extra_kwargs


class LDAPProviderViewSet(UsedByMixin, ModelViewSet):
    """LDAPProvider Viewset"""

    queryset = LDAPProvider.objects.all()
    serializer_class = LDAPProviderSerializer
    filterset_fields = {
        "application": ["isnull"],
        "name": ["iexact"],
        "authorization_flow__slug": ["iexact"],
        "base_dn": ["iexact"],
        "search_group__group_uuid": ["iexact"],
        "search_group__name": ["iexact"],
        "certificate__kp_uuid": ["iexact"],
        "certificate__name": ["iexact"],
        "tls_server_name": ["iexact"],
        "uid_start_number": ["iexact"],
        "gid_start_number": ["iexact"],
    }
    search_fields = ["name"]
    ordering = ["name"]


class LDAPOutpostConfigSerializer(ModelSerializer):
    """LDAPProvider Serializer"""

    application_slug = SerializerMethodField()
    bind_flow_slug = CharField(source="authorization_flow.slug")

    def get_application_slug(self, instance: LDAPProvider) -> str:
        """Prioritise backchannel slug over direct application slug"""
        if instance.backchannel_application:
            return instance.backchannel_application.slug
        return instance.application.slug

    class Meta:
        model = LDAPProvider
        fields = [
            "pk",
            "name",
            "base_dn",
            "bind_flow_slug",
            "application_slug",
            "search_group",
            "certificate",
            "tls_server_name",
            "uid_start_number",
            "gid_start_number",
            "search_mode",
            "bind_mode",
        ]


class LDAPOutpostConfigViewSet(ReadOnlyModelViewSet):
    """LDAPProvider Viewset"""

    queryset = LDAPProvider.objects.filter(application__isnull=False)
    serializer_class = LDAPOutpostConfigSerializer
    ordering = ["name"]
    search_fields = ["name"]
    filterset_fields = ["name"]
