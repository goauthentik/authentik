"""ProxyProvider API Views"""
from typing import Any, Optional

from drf_spectacular.utils import extend_schema_field
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, ListField, ReadOnlyField, SerializerMethodField
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import PassiveSerializer
from authentik.lib.utils.time import timedelta_from_string
from authentik.providers.oauth2.models import ScopeMapping
from authentik.providers.oauth2.views.provider import ProviderInfoView
from authentik.providers.proxy.models import ProxyMode, ProxyProvider


class OpenIDConnectConfigurationSerializer(PassiveSerializer):
    """rest_framework Serializer for OIDC Configuration"""

    issuer = CharField()
    authorization_endpoint = CharField()
    token_endpoint = CharField()
    userinfo_endpoint = CharField()
    end_session_endpoint = CharField()
    introspection_endpoint = CharField()
    jwks_uri = CharField()

    response_types_supported = ListField(child=CharField())
    id_token_signing_alg_values_supported = ListField(child=CharField())
    subject_types_supported = ListField(child=CharField())
    token_endpoint_auth_methods_supported = ListField(child=CharField())


class ProxyProviderSerializer(ProviderSerializer):
    """ProxyProvider Serializer"""

    redirect_uris = CharField(read_only=True)
    outpost_set = ListField(child=CharField(), read_only=True, source="outpost_set.all")

    def validate(self, attrs) -> dict[Any, str]:
        """Check that internal_host is set when mode is Proxy"""
        if (
            attrs.get("mode", ProxyMode.PROXY) == ProxyMode.PROXY
            and attrs.get("internal_host", "") == ""
        ):
            raise ValidationError("Internal host cannot be empty when forward auth is disabled.")
        return attrs

    def create(self, validated_data):
        instance: ProxyProvider = super().create(validated_data)
        instance.set_oauth_defaults()
        instance.save()
        return instance

    def update(self, instance: ProxyProvider, validated_data):
        instance = super().update(instance, validated_data)
        instance.set_oauth_defaults()
        instance.save()
        return instance

    class Meta:

        model = ProxyProvider
        fields = ProviderSerializer.Meta.fields + [
            "internal_host",
            "external_host",
            "internal_host_ssl_validation",
            "certificate",
            "skip_path_regex",
            "basic_auth_enabled",
            "basic_auth_password_attribute",
            "basic_auth_user_attribute",
            "mode",
            "redirect_uris",
            "cookie_domain",
            "token_validity",
            "outpost_set",
        ]


class ProxyProviderViewSet(UsedByMixin, ModelViewSet):
    """ProxyProvider Viewset"""

    queryset = ProxyProvider.objects.all()
    serializer_class = ProxyProviderSerializer
    filterset_fields = {
        "application": ["isnull"],
        "name": ["iexact"],
        "authorization_flow__slug": ["iexact"],
        "property_mappings": ["iexact"],
        "internal_host": ["iexact"],
        "external_host": ["iexact"],
        "internal_host_ssl_validation": ["iexact"],
        "certificate__kp_uuid": ["iexact"],
        "certificate__name": ["iexact"],
        "skip_path_regex": ["iexact"],
        "basic_auth_enabled": ["iexact"],
        "basic_auth_password_attribute": ["iexact"],
        "basic_auth_user_attribute": ["iexact"],
        "mode": ["iexact"],
        "redirect_uris": ["iexact"],
        "cookie_domain": ["iexact"],
    }
    search_fields = ["name"]
    ordering = ["name"]


class ProxyOutpostConfigSerializer(ModelSerializer):
    """Proxy provider serializer for outposts"""

    assigned_application_slug = ReadOnlyField(source="application.slug")
    assigned_application_name = ReadOnlyField(source="application.name")

    oidc_configuration = SerializerMethodField()
    token_validity = SerializerMethodField()
    scopes_to_request = SerializerMethodField()

    @extend_schema_field(OpenIDConnectConfigurationSerializer)
    def get_oidc_configuration(self, obj: ProxyProvider):
        """Embed OpenID Connect provider information"""
        return ProviderInfoView(request=self.context["request"]._request).get_info(obj)

    def get_token_validity(self, obj: ProxyProvider) -> Optional[float]:
        """Get token validity as second count"""
        return timedelta_from_string(obj.token_validity).total_seconds()

    def get_scopes_to_request(self, obj: ProxyProvider) -> list[str]:
        """Get all the scope names the outpost should request,
        including custom-defined ones"""
        scope_names = set(
            ScopeMapping.objects.filter(provider__in=[obj]).values_list("scope_name", flat=True)
        )
        return list(scope_names)

    class Meta:

        model = ProxyProvider
        fields = [
            "pk",
            "name",
            "internal_host",
            "external_host",
            "internal_host_ssl_validation",
            "client_id",
            "client_secret",
            "oidc_configuration",
            "cookie_secret",
            "certificate",
            "skip_path_regex",
            "basic_auth_enabled",
            "basic_auth_password_attribute",
            "basic_auth_user_attribute",
            "mode",
            "cookie_domain",
            "token_validity",
            "scopes_to_request",
            "assigned_application_slug",
            "assigned_application_name",
        ]


class ProxyOutpostConfigViewSet(ReadOnlyModelViewSet):
    """ProxyProvider Viewset"""

    queryset = ProxyProvider.objects.filter(application__isnull=False)
    serializer_class = ProxyOutpostConfigSerializer
    ordering = ["name"]
    search_fields = ["name"]
    filterset_fields = ["name"]
