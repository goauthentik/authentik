"""SAMLProvider API Views"""
from xml.etree.ElementTree import ParseError  # nosec

from defusedxml.ElementTree import fromstring
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.fields import CharField, FileField, ReadOnlyField
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.relations import SlugRelatedField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.viewsets import ModelViewSet
from structlog.stdlib import get_logger

from authentik.api.decorators import permission_required
from authentik.core.api.propertymappings import PropertyMappingSerializer
from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.utils import PassiveSerializer
from authentik.core.models import Provider
from authentik.flows.models import Flow, FlowDesignation
from authentik.providers.saml.models import SAMLPropertyMapping, SAMLProvider
from authentik.providers.saml.processors.metadata import MetadataProcessor
from authentik.providers.saml.processors.metadata_parser import (
    ServiceProviderMetadataParser,
)

LOGGER = get_logger()


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
            "sp_binding",
        ]


class SAMLMetadataSerializer(PassiveSerializer):
    """SAML Provider Metadata serializer"""

    metadata = ReadOnlyField()
    download_url = ReadOnlyField(required=False)


class SAMLProviderImportSerializer(PassiveSerializer):
    """Import saml provider from XML Metadata"""

    name = CharField(required=True)
    # Using SlugField because https://github.com/OpenAPITools/openapi-generator/issues/3278
    authorization_flow = SlugRelatedField(
        queryset=Flow.objects.filter(designation=FlowDesignation.AUTHORIZATION),
        slug_field="slug",
    )
    file = FileField()


from authentik.core.api.used_by import UsedByMixin


class SAMLProviderViewSet(UsedByMixin, ModelViewSet):
    """SAMLProvider Viewset"""

    queryset = SAMLProvider.objects.all()
    serializer_class = SAMLProviderSerializer

    @extend_schema(
        responses={
            200: SAMLMetadataSerializer(many=False),
            404: OpenApiResponse(description="Provider has no application assigned"),
        },
        parameters=[
            OpenApiParameter(
                name="download",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.BOOL,
            )
        ],
    )
    @action(methods=["GET"], detail=True, permission_classes=[AllowAny])
    # pylint: disable=invalid-name, unused-argument
    def metadata(self, request: Request, pk: int) -> Response:
        """Return metadata as XML string"""
        # We don't use self.get_object() on purpose as this view is un-authenticated
        provider = get_object_or_404(SAMLProvider, pk=pk)
        try:
            metadata = MetadataProcessor(provider, request).build_entity_descriptor()
            if "download" in request._request.GET:
                response = HttpResponse(metadata, content_type="application/xml")
                response[
                    "Content-Disposition"
                ] = f'attachment; filename="{provider.name}_authentik_meta.xml"'
                return response
            return Response({"metadata": metadata})
        except Provider.application.RelatedObjectDoesNotExist:  # pylint: disable=no-member
            return Response({"metadata": ""})

    @permission_required(
        None,
        [
            "authentik_providers_saml.add_samlprovider",
            "authentik_crypto.add_certificatekeypair",
        ],
    )
    @extend_schema(
        request={
            "multipart/form-data": SAMLProviderImportSerializer,
        },
        responses={
            204: OpenApiResponse(description="Successfully imported provider"),
            400: OpenApiResponse(description="Bad request"),
        },
    )
    @action(detail=False, methods=["POST"], parser_classes=(MultiPartParser,))
    def import_metadata(self, request: Request) -> Response:
        """Create provider from SAML Metadata"""
        data = SAMLProviderImportSerializer(data=request.data)
        if not data.is_valid():
            raise ValidationError(data.errors)
        file = data.validated_data["file"]
        # Validate syntax first
        try:
            fromstring(file.read())
        except ParseError:
            raise ValidationError(_("Invalid XML Syntax"))
        file.seek(0)
        try:
            metadata = ServiceProviderMetadataParser().parse(file.read().decode())
            metadata.to_provider(
                data.validated_data["name"], data.validated_data["authorization_flow"]
            )
        except ValueError as exc:  # pragma: no cover
            LOGGER.warning(str(exc))
            return ValidationError(
                _("Failed to import Metadata: %(message)s" % {"message": str(exc)}),
            )
        return Response(status=204)


class SAMLPropertyMappingSerializer(PropertyMappingSerializer):
    """SAMLPropertyMapping Serializer"""

    class Meta:

        model = SAMLPropertyMapping
        fields = PropertyMappingSerializer.Meta.fields + [
            "saml_name",
            "friendly_name",
        ]


from authentik.core.api.used_by import UsedByMixin


class SAMLPropertyMappingViewSet(UsedByMixin, ModelViewSet):
    """SAMLPropertyMapping Viewset"""

    queryset = SAMLPropertyMapping.objects.all()
    serializer_class = SAMLPropertyMappingSerializer
