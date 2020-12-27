"""OAuth2Provider API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.utils import MetaNameSerializer
from authentik.providers.oauth2.models import OAuth2Provider, ScopeMapping


class OAuth2ProviderSerializer(ModelSerializer, MetaNameSerializer):
    """OAuth2Provider Serializer"""

    class Meta:

        model = OAuth2Provider
        fields = [
            "pk",
            "name",
            "authorization_flow",
            "client_type",
            "client_id",
            "client_secret",
            "token_validity",
            "include_claims_in_id_token",
            "jwt_alg",
            "rsa_key",
            "redirect_uris",
            "sub_mode",
            "property_mappings",
            "issuer_mode",
            "verbose_name",
            "verbose_name_plural",
        ]


class OAuth2ProviderViewSet(ModelViewSet):
    """OAuth2Provider Viewset"""

    queryset = OAuth2Provider.objects.all()
    serializer_class = OAuth2ProviderSerializer


class ScopeMappingSerializer(ModelSerializer):
    """ScopeMapping Serializer"""

    class Meta:

        model = ScopeMapping
        fields = ["pk", "name", "scope_name", "description", "expression"]


class ScopeMappingViewSet(ModelViewSet):
    """ScopeMapping Viewset"""

    queryset = ScopeMapping.objects.all()
    serializer_class = ScopeMappingSerializer
