"""OAuth2Provider API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.providers.oauth2.models import OAuth2Provider, ScopeMapping


class OAuth2ProviderSerializer(ModelSerializer):
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
            "response_type",
            "jwt_alg",
            "rsa_key",
            "redirect_uris",
            "sub_mode",
            "property_mappings",
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
