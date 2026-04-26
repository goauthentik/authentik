"""SAMLSource API Views"""

from xml.etree.ElementTree import ParseError  # nosec

from defusedxml.ElementTree import fromstring
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import (
    BooleanField,
    CharField,
    FileField,
    PrimaryKeyRelatedField,
    ValidationError,
)
from rest_framework.viewsets import ModelViewSet

from authentik.api.validation import validate
from authentik.core.api.sources import SourceSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import PassiveSerializer
from authentik.crypto.models import CertificateKeyPair
from authentik.flows.models import Flow
from authentik.providers.saml.api.providers import SAMLMetadataSerializer
from authentik.rbac.decorators import permission_required
from authentik.sources.saml.models import SAMLSource
from authentik.sources.saml.processors.metadata import MetadataProcessor
from authentik.sources.saml.processors.metadata_parser import IdentityProviderMetadataParser


class SAMLSourceSerializer(SourceSerializer):
    """SAMLSource Serializer"""

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
        return super().validate(attrs)

    class Meta:
        model = SAMLSource
        fields = SourceSerializer.Meta.fields + [
            "group_matching_mode",
            "pre_authentication_flow",
            "issuer",
            "sso_url",
            "slo_url",
            "allow_idp_initiated",
            "force_authn",
            "name_id_policy",
            "binding_type",
            "verification_kp",
            "signing_kp",
            "verification_kp_ring",
            "signing_kp_ring",
            "encryption_kp",
            "encryption_kp_ring",
            "digest_algorithm",
            "signature_algorithm",
            "temporary_user_delete_after",
            "signed_assertion",
            "signed_response",
        ]


class SAMLSourceImportSerializer(PassiveSerializer):
    """Import SAML source from IdP XML Metadata"""

    source = PrimaryKeyRelatedField(
        queryset=SAMLSource.objects.all(),
        required=False,
        allow_null=True,
    )
    name = CharField(required=True, allow_blank=False)
    pre_authentication_flow = PrimaryKeyRelatedField(
        queryset=Flow.objects.all(),
        required=False,
        allow_null=True,
    )
    file = FileField(required=True)

    signing_certificate = PrimaryKeyRelatedField(
        queryset=CertificateKeyPair.objects.all(),
        required=False,
        allow_null=True,
    )

    create_missing_rings = BooleanField(required=False, default=True)

    def validate(self, attrs: dict):
        target = attrs.get("source")
        if target:
            return attrs

        missing = {}
        if not attrs.get("name"):
            missing["name"] = "This field is required when source is not set."
        if not attrs.get("pre_authentication_flow"):
            missing["pre_authentication_flow"] = (
                "This field is required when source is not set."
            )
        if missing:
            raise ValidationError(missing)
        return attrs


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
        "issuer",
        "sso_url",
        "slo_url",
        "allow_idp_initiated",
        "force_authn",
        "name_id_policy",
        "binding_type",
        "verification_kp",
        "verification_kp_ring",
        "signing_kp",
        "signing_kp_ring",
        "encryption_kp",
        "encryption_kp_ring",
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

    @permission_required(
        None,
        [
            "authentik_sources_saml.add_samlsource",
            "authentik_crypto.add_certificatekeypair",
        ],
    )
    @extend_schema(
        request={
            "multipart/form-data": SAMLSourceImportSerializer,
        },
        responses={
            201: SAMLSourceSerializer,
            400: None,
        },
    )
    @action(detail=False, methods=["POST"], parser_classes=(MultiPartParser,))
    @validate(SAMLSourceImportSerializer)
    def import_metadata(self, request: Request, body: SAMLSourceImportSerializer) -> Response:
        """Create source from IdP SAML metadata, or apply to an existing source."""
        file = body.validated_data["file"]

        try:
            fromstring(file.read())
        except ParseError:
            raise ValidationError(_("Invalid XML Syntax")) from None
        file.seek(0)

        try:
            sig_cert = body.validated_data.get("signing_certificate")
            metadata = IdentityProviderMetadataParser(signing_certificate=sig_cert).parse(
                file.read().decode()
            )

            target: SAMLSource | None = body.validated_data.get("source")
            name: str = body.validated_data["name"]
            create_missing_rings: bool = body.validated_data.get("create_missing_rings", True)

            if target is not None:
                if not (
                    request.user.has_perm("authentik_sources_saml.change_samlsource")
                    or request.user.has_perm("authentik_sources_saml.change_samlsource", target)
                ):
                    raise PermissionDenied()
                if target.name != name:
                    target.name = name
                    target.save(update_fields=["name"])

                metadata.apply_to_source(
                    target,
                    create_missing_rings=create_missing_rings,
                )
                return Response(
                    SAMLSourceSerializer(target, context={"request": request}).data,
                    status=200,
                )
            source = metadata.to_source(
                name=name,
                pre_authentication_flow=body.validated_data["pre_authentication_flow"],
            )
            return Response(
                SAMLSourceSerializer(source, context={"request": request}).data,
                status=201,
            )
        except ValueError as exc:
            raise ValidationError(
                _("Failed to import Metadata: {messages}".format_map({"messages": str(exc)}))
            ) from None
