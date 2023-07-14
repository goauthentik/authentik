"""LDAPProvider API Views"""
from django.db.models import QuerySet
from django.db.models.query import Q
from django_filters.filters import BooleanFilter
from django_filters.filterset import FilterSet
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
            "mfa_support",
        ]
        extra_kwargs = ProviderSerializer.Meta.extra_kwargs


class LDAPProviderFilter(FilterSet):
    """LDAP Provider filters"""

    application__isnull = BooleanFilter(method="filter_application__isnull")

    def filter_application__isnull(self, queryset: QuerySet, name, value):
        """Only return providers that are neither assigned to application,
        both as provider or application provider"""
        return queryset.filter(
            Q(backchannel_application__isnull=value) | Q(application__isnull=value)
        )

    class Meta:
        model = LDAPProvider
        fields = {
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


class LDAPProviderViewSet(UsedByMixin, ModelViewSet):
    """LDAPProvider Viewset"""

    queryset = LDAPProvider.objects.all()
    serializer_class = LDAPProviderSerializer
    filterset_class = LDAPProviderFilter
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
            "mfa_support",
        ]


class LDAPOutpostConfigViewSet(ReadOnlyModelViewSet):
    """LDAPProvider Viewset"""

    queryset = LDAPProvider.objects.filter(
        Q(application__isnull=False) | Q(backchannel_application__isnull=False)
    )
    serializer_class = LDAPOutpostConfigSerializer
    ordering = ["name"]
    search_fields = ["name"]
    filterset_fields = ["name"]
