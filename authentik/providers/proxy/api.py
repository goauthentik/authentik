"""ProxyProvider API Views"""
from drf_yasg2.utils import swagger_serializer_method
from rest_framework.fields import CharField, ListField, ReadOnlyField, SerializerMethodField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.utils import MetaNameSerializer
from authentik.providers.oauth2.views.provider import ProviderInfoView
from authentik.providers.proxy.models import ProxyProvider


class OpenIDConnectConfigurationSerializer(Serializer):
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

    def create(self, request: Request) -> Response:
        raise NotImplementedError

    def update(self, request: Request) -> Response:
        raise NotImplementedError


class ProxyProviderSerializer(MetaNameSerializer, ModelSerializer):
    """ProxyProvider Serializer"""

    assigned_application_slug = ReadOnlyField(source="application.slug")
    assigned_application_name = ReadOnlyField(source="application.name")

    def create(self, validated_data):
        instance: ProxyProvider = super().create(validated_data)
        instance.set_oauth_defaults()
        instance.save()
        return instance

    def update(self, instance: ProxyProvider, validated_data):
        instance.set_oauth_defaults()
        return super().update(instance, validated_data)

    class Meta:

        model = ProxyProvider
        fields = [
            "pk",
            "name",
            "internal_host",
            "external_host",
            "internal_host_ssl_validation",
            "certificate",
            "skip_path_regex",
            "basic_auth_enabled",
            "basic_auth_password_attribute",
            "basic_auth_user_attribute",
            "assigned_application_slug",
            "assigned_application_name",
            "verbose_name",
            "verbose_name_plural",
        ]


class ProxyProviderViewSet(ModelViewSet):
    """ProxyProvider Viewset"""

    queryset = ProxyProvider.objects.all()
    serializer_class = ProxyProviderSerializer


class ProxyOutpostConfigSerializer(ModelSerializer):
    """ProxyProvider Serializer"""

    oidc_configuration = SerializerMethodField()

    def create(self, validated_data):
        instance: ProxyProvider = super().create(validated_data)
        instance.set_oauth_defaults()
        instance.save()
        return instance

    def update(self, instance: ProxyProvider, validated_data):
        instance.set_oauth_defaults()
        return super().update(instance, validated_data)

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
        ]

    @swagger_serializer_method(serializer_or_field=OpenIDConnectConfigurationSerializer)
    def get_oidc_configuration(self, obj: ProxyProvider):
        """Embed OpenID Connect provider information"""
        return ProviderInfoView(request=self.context["request"]._request).get_info(obj)


class ProxyOutpostConfigViewSet(ModelViewSet):
    """ProxyProvider Viewset"""

    queryset = ProxyProvider.objects.filter(application__isnull=False)
    serializer_class = ProxyOutpostConfigSerializer
