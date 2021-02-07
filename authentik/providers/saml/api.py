"""SAMLProvider API Views"""
from drf_yasg2.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.fields import ReadOnlyField
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.utils import MetaNameSerializer
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

    @action(methods=["GET"], detail=True)
    @swagger_auto_schema(responses={200: SAMLMetadataSerializer(many=False)})
    # pylint: disable=invalid-name
    def metadata(self, request: Request, pk: int) -> str:
        """Return metadata as XML string"""
        provider = get_object_or_404(SAMLProvider, pk=pk)
        metadata = DescriptorDownloadView.get_metadata(request, provider)
        return Response({"metadata": metadata})


class SAMLPropertyMappingSerializer(ModelSerializer, MetaNameSerializer):
    """SAMLPropertyMapping Serializer"""

    class Meta:

        model = SAMLPropertyMapping
        fields = [
            "pk",
            "name",
            "saml_name",
            "friendly_name",
            "expression",
            "verbose_name",
            "verbose_name_plural",
        ]


class SAMLPropertyMappingViewSet(ModelViewSet):
    """SAMLPropertyMapping Viewset"""

    queryset = SAMLPropertyMapping.objects.all()
    serializer_class = SAMLPropertyMappingSerializer
