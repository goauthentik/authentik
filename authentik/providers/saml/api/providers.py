"""SAMLProvider API Views"""
from xml.etree.ElementTree import ParseError  # nosec

from defusedxml.ElementTree import fromstring
from django.http import HttpRequest
from django.http.response import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.fields import CharField, FileField, SerializerMethodField
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import PrimaryKeyRelatedField, ValidationError
from rest_framework.viewsets import ModelViewSet
from structlog.stdlib import get_logger

from authentik.api.decorators import permission_required
from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import PassiveSerializer, PropertyMappingPreviewSerializer
from authentik.core.models import Provider
from authentik.flows.models import Flow, FlowDesignation
from authentik.providers.saml.models import SAMLProvider
from authentik.providers.saml.processors.assertion import AssertionProcessor
from authentik.providers.saml.processors.authn_request_parser import AuthNRequest
from authentik.providers.saml.processors.metadata import MetadataProcessor
from authentik.providers.saml.processors.metadata_parser import ServiceProviderMetadataParser
from authentik.sources.saml.processors.constants import SAML_BINDING_POST, SAML_BINDING_REDIRECT

LOGGER = get_logger()


class SAMLProviderSerializer(ProviderSerializer):
    """SAMLProvider Serializer"""

    url_download_metadata = SerializerMethodField()

    url_sso_post = SerializerMethodField()
    url_sso_redirect = SerializerMethodField()
    url_sso_init = SerializerMethodField()
    url_slo_post = SerializerMethodField()
    url_slo_redirect = SerializerMethodField()

    def get_url_download_metadata(self, instance: SAMLProvider) -> str:
        """Get metadata download URL"""
        if "request" not in self._context:
            return ""
        request: HttpRequest = self._context["request"]._request
        return request.build_absolute_uri(
            reverse("authentik_api:samlprovider-metadata", kwargs={"pk": instance.pk}) + "?download"
        )

    def get_url_sso_post(self, instance: SAMLProvider) -> str:
        """Get SSO Post URL"""
        if "request" not in self._context:
            return ""
        request: HttpRequest = self._context["request"]._request
        try:
            return request.build_absolute_uri(
                reverse(
                    "authentik_providers_saml:sso-post",
                    kwargs={"application_slug": instance.application.slug},
                )
            )
        except Provider.application.RelatedObjectDoesNotExist:  # pylint: disable=no-member
            return "-"

    def get_url_sso_redirect(self, instance: SAMLProvider) -> str:
        """Get SSO Redirect URL"""
        if "request" not in self._context:
            return ""
        request: HttpRequest = self._context["request"]._request
        try:
            return request.build_absolute_uri(
                reverse(
                    "authentik_providers_saml:sso-redirect",
                    kwargs={"application_slug": instance.application.slug},
                )
            )
        except Provider.application.RelatedObjectDoesNotExist:  # pylint: disable=no-member
            return "-"

    def get_url_sso_init(self, instance: SAMLProvider) -> str:
        """Get SSO IDP-Initiated URL"""
        if "request" not in self._context:
            return ""
        request: HttpRequest = self._context["request"]._request
        try:
            return request.build_absolute_uri(
                reverse(
                    "authentik_providers_saml:sso-init",
                    kwargs={"application_slug": instance.application.slug},
                )
            )
        except Provider.application.RelatedObjectDoesNotExist:  # pylint: disable=no-member
            return "-"

    def get_url_slo_post(self, instance: SAMLProvider) -> str:
        """Get SLO POST URL"""
        if "request" not in self._context:
            return ""
        request: HttpRequest = self._context["request"]._request
        try:
            return request.build_absolute_uri(
                reverse(
                    "authentik_providers_saml:slo-post",
                    kwargs={"application_slug": instance.application.slug},
                )
            )
        except Provider.application.RelatedObjectDoesNotExist:  # pylint: disable=no-member
            return "-"

    def get_url_slo_redirect(self, instance: SAMLProvider) -> str:
        """Get SLO redirect URL"""
        if "request" not in self._context:
            return ""
        request: HttpRequest = self._context["request"]._request
        try:
            return request.build_absolute_uri(
                reverse(
                    "authentik_providers_saml:slo-redirect",
                    kwargs={"application_slug": instance.application.slug},
                )
            )
        except Provider.application.RelatedObjectDoesNotExist:  # pylint: disable=no-member
            return "-"

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
            "url_download_metadata",
            "url_sso_post",
            "url_sso_redirect",
            "url_sso_init",
            "url_slo_post",
            "url_slo_redirect",
        ]
        extra_kwargs = ProviderSerializer.Meta.extra_kwargs


class SAMLMetadataSerializer(PassiveSerializer):
    """SAML Provider Metadata serializer"""

    metadata = CharField(read_only=True)
    download_url = CharField(read_only=True, required=False)


class SAMLProviderImportSerializer(PassiveSerializer):
    """Import saml provider from XML Metadata"""

    name = CharField(required=True)
    authorization_flow = PrimaryKeyRelatedField(
        queryset=Flow.objects.filter(designation=FlowDesignation.AUTHORIZATION),
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
                description="Optionally force the metadata to only include one binding.",
            ),
        ],
    )
    @action(methods=["GET"], detail=True, permission_classes=[AllowAny])
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

    @permission_required(
        "authentik_providers_saml.view_samlprovider",
    )
    @extend_schema(
        responses={
            200: PropertyMappingPreviewSerializer(),
            400: OpenApiResponse(description="Bad request"),
        },
    )
    @action(detail=True, methods=["GET"])
    def preview_user(self, request: Request, pk: int) -> Response:
        """Preview user data for provider"""
        provider: SAMLProvider = self.get_object()
        processor = AssertionProcessor(provider, request._request, AuthNRequest())
        attributes = processor.get_attributes()
        name_id = processor.get_name_id()
        data = []
        for attribute in attributes:
            item = {"Value": []}
            item.update(attribute.attrib)
            for value in attribute:
                item["Value"].append(value.text)
            data.append(item)
        serializer = PropertyMappingPreviewSerializer(
            instance={"preview": {"attributes": data, "nameID": name_id.text}}
        )
        return Response(serializer.data)
