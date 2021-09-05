"""LDAPProvider API Views"""
from rest_framework.fields import CharField
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.providers.ldap.models import LDAPProvider


class LDAPProviderSerializer(ProviderSerializer):
    """LDAPProvider Serializer"""

    class Meta:

        model = LDAPProvider
        fields = ProviderSerializer.Meta.fields + [
            "base_dn",
            "search_group",
            "certificate",
            "tls_server_name",
            "uid_start_number",
            "gid_start_number",
        ]


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
    ordering = ["name"]


class LDAPOutpostConfigSerializer(ModelSerializer):
    """LDAPProvider Serializer"""

    application_slug = CharField(source="application.slug")
    bind_flow_slug = CharField(source="authorization_flow.slug")

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
        ]


class LDAPOutpostConfigViewSet(ReadOnlyModelViewSet):
    """LDAPProvider Viewset"""

    queryset = LDAPProvider.objects.filter(application__isnull=False)
    serializer_class = LDAPOutpostConfigSerializer
    ordering = ["name"]
