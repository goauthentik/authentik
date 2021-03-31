"""SAMLProvider API Views"""
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.fields import ReadOnlyField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.propertymappings import PropertyMappingSerializer
from authentik.core.api.providers import ProviderSerializer
from authentik.core.models import Provider
from authentik.providers.saml.models import SAMLPropertyMapping, SAMLProvider
from authentik.providers.saml.views.metadata import DescriptorDownloadView


class SAMLProviderSerializer(ProviderSerializer):
    """SAMLProvider Serializer"""

    class Meta:

        model = SAMLProvider
        fields = ProviderSerializer.Meta.fields + [
            "acs_url",
            "audience",
            "issuer",
            "assertion_valid_not_before",
            "assertion_valid_not_on_or_after",
            "session_valid_not_on_or_after",
            "property_mappings",
            "name_id_mapping",
            "digest_algorithm",
            "signature_algorithm",
            "signing_kp",
            "verification_kp",
        ]


class SAMLMetadataSerializer(Serializer):
    """SAML Provider Metadata serializer"""

    metadata = ReadOnlyField()

    def create(self, request: Request) -> Response:
        raise NotImplementedError

    def update(self, request: Request) -> Response:
        raise NotImplementedError


class SAMLProviderViewSet(ModelViewSet):
    """SAMLProvider Viewset"""

    queryset = SAMLProvider.objects.all()
    serializer_class = SAMLProviderSerializer

    @swagger_auto_schema(responses={200: SAMLMetadataSerializer(many=False)})
    @action(methods=["GET"], detail=True)
    # pylint: disable=invalid-name, unused-argument
    def metadata(self, request: Request, pk: int) -> Response:
        """Return metadata as XML string"""
        provider = self.get_object()
        try:
            metadata = DescriptorDownloadView.get_metadata(request, provider)
            return Response({"metadata": metadata})
        except Provider.application.RelatedObjectDoesNotExist:  # pylint: disable=no-member
            return Response({"metadata": ""})


class SAMLPropertyMappingSerializer(PropertyMappingSerializer):
    """SAMLPropertyMapping Serializer"""

    class Meta:

        model = SAMLPropertyMapping
        fields = PropertyMappingSerializer.Meta.fields + [
            "saml_name",
            "friendly_name",
        ]


class SAMLPropertyMappingViewSet(ModelViewSet):
    """SAMLPropertyMapping Viewset"""

    queryset = SAMLPropertyMapping.objects.all()
    serializer_class = SAMLPropertyMappingSerializer
