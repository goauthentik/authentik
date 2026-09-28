"""SAMLSource API Views"""

from xml.etree.ElementTree import ParseError  # nosec

from defusedxml.ElementTree import fromstring
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.fields import SerializerMethodField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.viewsets import ModelViewSet

from authentik.common.saml.metadata import MetadataFetchError, fetch_metadata
from authentik.core.api.sources import SourceSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.providers.saml.api.providers import SAMLMetadataSerializer
from authentik.sources.saml.models import SAMLSource
from authentik.sources.saml.processors.metadata import MetadataProcessor
from authentik.sources.saml.processors.metadata_parser import (
    IdentityProviderMetadata,
    IdentityProviderMetadataParser,
)


def fetch_and_parse_metadata(url: str) -> IdentityProviderMetadata:
    """Download and parse IdP metadata from `url`, converting errors to validation errors"""
    try:
        raw_metadata = fetch_metadata(url)
    except MetadataFetchError as exc:
        raise ValidationError({"metadata_url": str(exc)}) from None
    try:
        fromstring(raw_metadata)
    except ParseError:
        raise ValidationError({"metadata_url": _("Invalid XML Syntax")}) from None
    try:
        return IdentityProviderMetadataParser().parse(raw_metadata)
    except (ValueError, KeyError) as exc:
        raise ValidationError(
            {"metadata_url": _("Failed to parse metadata: {message}").format(message=str(exc))}
        ) from None


class SAMLSourceSerializer(SourceSerializer):
    """SAMLSource Serializer."""

    url_issuer = SerializerMethodField()

    _metadata: IdentityProviderMetadata | None = None

    def get_url_issuer(self, instance: SAMLSource) -> str:
        """Get the resolved Issuer, falling back to the metadata URL when unset"""
        if "request" not in self._context:
            return instance.issuer_override or ""
        return instance.get_issuer(self._context["request"]._request)

    def validate(self, attrs: dict):
        if attrs.get("verification_kp"):
            if not attrs.get("signed_assertion") and not attrs.get("signed_response"):
                raise ValidationError(
                    _(
                        "With a Verification Certificate selected, at least one of"
                        " 'Verify Assertion Signature' or 'Verify Response Signature' "
                        "must be selected."
                    )
                )
        metadata_url = attrs.get("metadata_url", "")
        previous_url = self.instance.metadata_url if self.instance else ""
        if metadata_url and metadata_url != previous_url:
            self._metadata = fetch_and_parse_metadata(metadata_url)
        has_sso_url = bool(attrs.get("sso_url") or (self.instance and self.instance.sso_url))
        if not has_sso_url and not metadata_url:
            raise ValidationError(
                {"sso_url": _("Either an SSO URL or a metadata URL is required.")}
            )
        return super().validate(attrs)

    def _apply_metadata(self, instance: SAMLSource) -> SAMLSource:
        if self._metadata and self._metadata.apply_to_source(instance):
            instance.save()
        return instance

    def create(self, validated_data: dict) -> SAMLSource:
        return self._apply_metadata(super().create(validated_data))

    def update(self, instance: SAMLSource, validated_data: dict) -> SAMLSource:
        return self._apply_metadata(super().update(instance, validated_data))

    class Meta:
        model = SAMLSource
        fields = SourceSerializer.Meta.fields + [
            "group_matching_mode",
            "pre_authentication_flow",
            "issuer_override",
            "url_issuer",
            "metadata_url",
            "sso_url",
            "slo_url",
            "allow_idp_initiated",
            "force_authn",
            "name_id_policy",
            "binding_type",
            "verification_kp",
            "signing_kp",
            "digest_algorithm",
            "signature_algorithm",
            "temporary_user_delete_after",
            "encryption_kp",
            "signed_assertion",
            "signed_response",
        ]
        extra_kwargs = {
            # Filled in from the metadata when a metadata URL is given
            "sso_url": {"required": False, "allow_blank": True},
        }


class SAMLSourceViewSet(UsedByMixin, ModelViewSet):
    """SAMLSource Viewset"""

    queryset = SAMLSource.objects.all()
    serializer_class = SAMLSourceSerializer
    lookup_field = "slug"
    filterset_fields = [
        "pbm_uuid",
        "name",
        "slug",
        "enabled",
        "authentication_flow",
        "enrollment_flow",
        "managed",
        "policy_engine_mode",
        "user_matching_mode",
        "pre_authentication_flow",
        "issuer_override",
        "metadata_url",
        "sso_url",
        "slo_url",
        "allow_idp_initiated",
        "force_authn",
        "name_id_policy",
        "binding_type",
        "verification_kp",
        "signing_kp",
        "digest_algorithm",
        "signature_algorithm",
        "temporary_user_delete_after",
        "signed_assertion",
        "signed_response",
    ]
    search_fields = ["name", "slug"]
    ordering = ["name"]

    @extend_schema(responses={200: SAMLMetadataSerializer(many=False)})
    @action(methods=["GET"], detail=True)
    def metadata(self, request: Request, slug: str) -> Response:
        """Return metadata as XML string"""
        source = self.get_object()
        metadata = MetadataProcessor(source, request).build_entity_descriptor()
        return Response(
            {
                "metadata": metadata,
                "download_url": reverse(
                    "authentik_sources_saml:metadata",
                    kwargs={
                        "source_slug": source.slug,
                    },
                ),
            }
        )
