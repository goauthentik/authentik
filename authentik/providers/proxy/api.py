"""ProxyProvider API Views"""
from typing import Any

from drf_spectacular.utils import extend_schema_field, extend_schema_serializer
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, ListField, SerializerMethodField
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import PassiveSerializer
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

    def validate(self, attrs) -> dict[Any, str]:
        """Check that internal_host is set when mode is Proxy"""
        if (
            attrs.get("mode", ProxyMode.PROXY) == ProxyMode.PROXY
            and attrs.get("internal_host", "") == ""
        ):
            raise ValidationError(
                "Internal host cannot be empty when forward auth is disabled."
            )
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
        ]


class ProxyProviderViewSet(UsedByMixin, ModelViewSet):
    """ProxyProvider Viewset"""

    queryset = ProxyProvider.objects.all()
    serializer_class = ProxyProviderSerializer
    ordering = ["name"]


@extend_schema_serializer(deprecate_fields=["forward_auth_mode"])
class ProxyOutpostConfigSerializer(ModelSerializer):
    """Proxy provider serializer for outposts"""

    oidc_configuration = SerializerMethodField()

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
        ]

    @extend_schema_field(OpenIDConnectConfigurationSerializer)
    def get_oidc_configuration(self, obj: ProxyProvider):
        """Embed OpenID Connect provider information"""
        return ProviderInfoView(request=self.context["request"]._request).get_info(obj)


class ProxyOutpostConfigViewSet(ReadOnlyModelViewSet):
    """ProxyProvider Viewset"""

    queryset = ProxyProvider.objects.filter(application__isnull=False)
    serializer_class = ProxyOutpostConfigSerializer
    ordering = ["name"]
