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
        ]


class LDAPProviderViewSet(UsedByMixin, ModelViewSet):
    """LDAPProvider Viewset"""

    queryset = LDAPProvider.objects.all()
    serializer_class = LDAPProviderSerializer
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
        ]


class LDAPOutpostConfigViewSet(ReadOnlyModelViewSet):
    """LDAPProvider Viewset"""

    queryset = LDAPProvider.objects.filter(application__isnull=False)
    serializer_class = LDAPOutpostConfigSerializer
    ordering = ["name"]
