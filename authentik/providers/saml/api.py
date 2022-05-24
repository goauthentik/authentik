"""SAMLProvider API Views"""
from xml.etree.ElementTree import ParseError  # nosec

from defusedxml.ElementTree import fromstring
from django.http.response import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_filters.filters import AllValuesMultipleFilter
from django_filters.filterset import FilterSet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_field,
)
from rest_framework.decorators import action
from rest_framework.fields import CharField, FileField, SerializerMethodField
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
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import PassiveSerializer
from authentik.core.models import Provider
from authentik.flows.models import Flow, FlowDesignation
from authentik.providers.saml.models import SAMLPropertyMapping, SAMLProvider
from authentik.providers.saml.processors.metadata import MetadataProcessor
from authentik.providers.saml.processors.metadata_parser import ServiceProviderMetadataParser
from authentik.sources.saml.processors.constants import SAML_BINDING_POST, SAML_BINDING_REDIRECT

LOGGER = get_logger()


class SAMLProviderSerializer(ProviderSerializer):
    """SAMLProvider Serializer"""

    metadata_download_url = SerializerMethodField()

    def get_metadata_download_url(self, instance: SAMLProvider) -> str:
        """Get metadata download URL"""
        return (
            reverse("authentik_api:samlprovider-metadata", kwargs={"pk": instance.pk}) + "?download"
        )

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
            "metadata_download_url",
        ]


class SAMLMetadataSerializer(PassiveSerializer):
    """SAML Provider Metadata serializer"""

    metadata = CharField(read_only=True)
    download_url = CharField(read_only=True, required=False)


class SAMLProviderImportSerializer(PassiveSerializer):
    """Import saml provider from XML Metadata"""

    name = CharField(required=True)
    # Using SlugField because https://github.com/OpenAPITools/openapi-generator/issues/3278
    authorization_flow = SlugRelatedField(
        queryset=Flow.objects.filter(designation=FlowDesignation.AUTHORIZATION),
        slug_field="slug",
    )
    file = FileField()


class SAMLProviderViewSet(UsedByMixin, ModelViewSet):
    """SAMLProvider Viewset"""

    queryset = SAMLProvider.objects.all()
    serializer_class = SAMLProviderSerializer
    filterset_fields = "__all__"
    ordering = ["name"]
    search_fields = ["name"]

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
            ),
            OpenApiParameter(
                name="force_binding",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                enum=[
                    SAML_BINDING_REDIRECT,
                    SAML_BINDING_POST,
                ],
                description=("Optionally force the metadata to only include one binding."),
            ),
        ],
    )
    @action(methods=["GET"], detail=True, permission_classes=[AllowAny])
    # pylint: disable=invalid-name, unused-argument
    def metadata(self, request: Request, pk: int) -> Response:
        """Return metadata as XML string"""
        # We don't use self.get_object() on purpose as this view is un-authenticated
        try:
            provider = get_object_or_404(SAMLProvider, pk=pk)
        except ValueError:
            raise Http404
        try:
            proc = MetadataProcessor(provider, request)
            proc.force_binding = request.query_params.get("force_binding", None)
            metadata = proc.build_entity_descriptor()
            if "download" in request.query_params:
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
            raise ValidationError(
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


class SAMLPropertyMappingFilter(FilterSet):
    """Filter for SAMLPropertyMapping"""

    managed = extend_schema_field(OpenApiTypes.STR)(AllValuesMultipleFilter(field_name="managed"))

    class Meta:
        model = SAMLPropertyMapping
        fields = "__all__"


class SAMLPropertyMappingViewSet(UsedByMixin, ModelViewSet):
    """SAMLPropertyMapping Viewset"""

    queryset = SAMLPropertyMapping.objects.all()
    serializer_class = SAMLPropertyMappingSerializer
    filterset_class = SAMLPropertyMappingFilter
    search_fields = ["name"]
    ordering = ["name"]
