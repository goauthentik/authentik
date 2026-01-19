"""WSFederationProvider API Views"""

from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.providers.ws_federation.models import WSFederationProvider
from authentik.enterprise.providers.ws_federation.processors.metadata import MetadataProcessor
from authentik.providers.saml.api.providers import SAMLProviderSerializer, SAMLProviderViewSet


class WSFederationProviderSerializer(EnterpriseRequiredMixin, SAMLProviderSerializer):
    """WSFederationProvider Serializer"""

    class Meta(SAMLProviderSerializer.Meta):
        model = WSFederationProvider


class WSFederationProviderViewSet(SAMLProviderViewSet):
    """WSFederationProvider Viewset"""

    queryset = WSFederationProvider.objects.all()
    serializer_class = WSFederationProviderSerializer
    filterset_fields = "__all__"
    ordering = ["name"]
    search_fields = ["name"]

    metadata_generator_class = MetadataProcessor
